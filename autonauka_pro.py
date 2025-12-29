"""
Autonauka Pro - Zaawansowany moduł do automatycznej nauki i wyszukiwania informacji
===============================================================================

Moduł zawiera funkcje do:
- Inteligentnego wyszukiwania w wielu źródłach (Google, Wikipedia, arXiv, Semantic Scholar)
- Analizy wiarygodności źródeł
- Ekstrakcji faktów z tekstu przy użyciu LLM
- Zarządzania pamięcią długoterminową
- Kompresji i optymalizacji treści

Główne funkcje:
- web_learn(): Główna funkcja do nauki z internetu
- news_search(): Wyszukiwanie aktualności sportowych
- normalize_scores(): Normalizacja wyników sportowych
"""

import asyncio
import contextlib
import dataclasses
import hashlib
import html
import json
import math
import os
import re
import time
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode, urlparse, parse_qsl, quote_plus

import httpx
from bs4 import BeautifulSoup
from readability import Document as ReadabilityDoc

# Importy z systemu Mordzix AI
from core.config import (
    SERPAPI_KEY, FIRECRAWL_KEY, WEB_USER_AGENT, HTTP_TIMEOUT,
    LLM_BASE_URL, LLM_API_KEY, LLM_MODEL
)
from core.llm import call_llm
from core.memory import ltm_add

# Stałe konfiguracyjne
WEB_HTTP_TIMEOUT = float(os.getenv("WEB_HTTP_TIMEOUT", "45"))
AUTO_TOPK = int(os.getenv("AUTO_TOPK", "8"))
AUTO_FETCH = int(os.getenv("AUTO_FETCH", "4"))
AUTO_MIN_CHARS = int(os.getenv("AUTO_MIN_CHARS", "800"))
AUTO_MAX_CHARS = int(os.getenv("AUTO_MAX_CHARS", "8000"))

AUTON_WAL = os.getenv("AUTON_WAL", "/workspace/mrd/data/mem/autonauka.wal")
AUTON_DEDUP_MAX = int(os.getenv("AUTON_DEDUP_MAX", "1000"))
AUTON_DOMAIN_MAX = int(os.getenv("AUTON_DOMAIN_MAX", "2"))
VOTE_MIN_SOURCES = int(os.getenv("VOTE_MIN_SOURCES", "2"))

AUTO_TAGS = os.getenv("AUTO_TAGS", "autonauka,web,evidence")

CONCURRENCY = int(os.getenv("AUTON_CONCURRENCY", "8"))
USER_AGENT = os.getenv("AUTON_UA", "Autonauka/1.0")

# Modele danych
@dataclass
class Material:
    title: Optional[str]
    url: Optional[str]
    domain: Optional[str]
    trust: Optional[float]
    recency: Optional[float]
    snippet: Optional[str]
    facts: Optional[List[str]]

@dataclass
class LearnResult:
    query: str
    count: int
    trust_avg: float
    backend: Optional[str]
    ltm_ids: List[str]
    citations: List[str]
    materials: List[Material]
    draft: Optional[str]

# Klasa do deduplikacji z LRU
class _LRUDedup:
    def __init__(self, cap: int):
        self.cap = cap
        self.order: List[str] = []
        self.set = set()

    def put(self, key: str) -> None:
        if key in self.set:
            with contextlib.suppress(ValueError):
                self.order.remove(key)
            self.order.append(key)
            return
        self.set.add(key)
        self.order.append(key)
        if len(self.order) > self.cap:
            old = self.order.pop(0)
            self.set.discard(old)

    def has(self, key: str) -> bool:
        return key in self.set

# Funkcje narzędziowe
def _normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()

def _norm_text(s: str) -> str:
    s = html.unescape(s or "")
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\u200b", "")
    return _normalize_ws(s)

def _canonical_url(url: str) -> str:
    try:
        p = urlparse(url)
        scheme = "https" if p.scheme in ("http", "https") else p.scheme
        query = urlencode([(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
                          if k not in {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "gclid", "fbclid", "igshid", "mc_cid", "mc_eid"}])
        path = re.sub(r"/+$", "", p.path or "")
        return urlunparse((scheme, p.netloc.lower(), path, "", query, ""))
    except Exception:
        return url

def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""

def _now_ts() -> float:
    return time.time()

def _parse_date_from_html(soup: BeautifulSoup) -> Optional[datetime]:
    for sel, attr in [
        ('meta[property="article:published_time"]', "content"),
        ('meta[name="pubdate"]', "content"),
        ('meta[name="date"]', "content"),
        ('time[datetime]', "datetime"),
        ('meta[itemprop="datePublished"]', "content"),
    ]:
        tag = soup.select_one(sel)
        if tag and tag.get(attr):
            with contextlib.suppress(Exception):
                return datetime.fromisoformat(tag.get(attr).replace("Z", "+00:00"))
    text = soup.get_text(" ", strip=True)
    m = re.search(r"(20\d{2}[-/\.]\d{1,2}[-/\.]\d{1,2})", text)
    if m:
        s = m.group(1).replace("/", "-").replace(".", "-")
        y, mn, dd = map(int, s.split("-"))
        with contextlib.suppress(Exception):
            return datetime(y, mn, dd, tzinfo=timezone.utc)
    return None

def _recency_score(dt: Optional[datetime]) -> float:
    if not dt:
        return 0.3
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=timezone.utc)
    days = max(1.0, (datetime.now(timezone.utc) - dt).total_seconds() / 86400.0)
    return max(0.2, 1.0 / math.log2(2 + days / 7))

def _client() -> httpx.AsyncClient:
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/json;q=0.9,*/*;q=0.8"}
    return httpx.AsyncClient(follow_redirects=True, timeout=WEB_HTTP_TIMEOUT, headers=headers)

# Funkcje wyszukiwania
async def _ddg_search(q: str, k: int) -> List[Tuple[str, str]]:
    url = "https://duckduckgo.com/html/"
    out: List[Tuple[str, str]] = []
    async with _client() as cl:
        r = await cl.post(url, data={"q": q})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.select("a.result__a"):
            href = a.get("href")
            title = _norm_text(a.text)
            if href and title:
                out.append((title, href))
            if len(out) >= k:
                break
    return out

async def _wiki_search(q: str, k: int) -> List[Tuple[str, str]]:
    api = "https://en.wikipedia.org/w/api.php"
    params = {"action": "opensearch", "format": "json", "limit": str(k), "search": q}
    async with _client() as cl:
        r = await cl.get(api, params=params)
        r.raise_for_status()
        js = r.json()
    return [(_norm_text(t), l) for t, l in zip(js[1], js[3])]

async def _arxiv_search(q: str, k: int) -> List[Tuple[str, str]]:
    api = "http://export.arxiv.org/api/query"
    params = {"search_query": q, "start": "0", "max_results": str(k)}
    async with _client() as cl:
        r = await cl.get(api, params=params)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "xml")
    out = []
    for e in soup.select("entry"):
        t = _norm_text(e.select_one("title").text if e.select_one("title") else "")
        link = e.select_one("id").text if e.select_one("id") else None
        if t and link:
            out.append((t, link))
    return out[:k]

async def _s2_search(q: str, k: int) -> List[Tuple[str, str]]:
    api = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {"query": q, "limit": str(k), "fields": "title,url"}
    async with _client() as cl:
        r = await cl.get(api, params=params)
        if r.status_code >= 400:
            return []
        js = r.json()
    out = []
    for it in js.get("data", []):
        t = _norm_text(it.get("title") or "")
        u = it.get("url")
        if t and u:
            out.append((t, u))
    return out

async def _serpapi_search(q: str, k: int) -> List[Tuple[str, str]]:
    if not SERPAPI_KEY:
        return []
    api = "https://serpapi.com/search.json"
    params = {"engine": "google", "q": q, "num": str(k), "api_key": SERPAPI_KEY}
    async with _client() as cl:
        r = await cl.get(api, params=params)
        if r.status_code >= 400:
            return []
        js = r.json()
    out = []
    for it in js.get("organic_results", []):
        t = _norm_text(it.get("title", ""))
        u = it.get("link")
        if t and u:
            out.append((t, u))
    return out[:k]

# Funkcje pobierania treści
async def _firecrawl(url: str) -> Optional[str]:
    if not FIRECRAWL_KEY:
        return None
    api = "https://api.firecrawl.dev/v1/scrape"
    payload = {"url": url, "formats": ["markdown", "html", "rawHtml"], "actions": []}
    headers = {"Authorization": f"Bearer {FIRECRAWL_KEY}", "Content-Type": "application/json"}
    async with _client() as cl:
        r = await cl.post(api, json=payload, headers=headers)
        if r.status_code >= 400:
            return None
        js = r.json()
    text = js.get("markdown") or js.get("html") or js.get("rawHtml")
    if not text:
        return None
    return _norm_text(BeautifulSoup(text, "html.parser").get_text(" "))

async def _http_text(url: str) -> Optional[Tuple[str, str, Optional[datetime]]]:
    async with _client() as cl:
        r = await cl.get(url)
        if r.status_code >= 400 or not r.text:
            return None
        html_txt = r.text
        doc = ReadabilityDoc(html_txt)
        title = _norm_text(doc.short_title() or "")
        article_html = doc.summary(html_partial=True)
        soup = BeautifulSoup(article_html, "html.parser")
        dt = _parse_date_from_html(soup)
        text = _norm_text(soup.get_text(" "))
        if len(text) < 200:
            soup2 = BeautifulSoup(html_txt, "html.parser")
            dt = dt or _parse_date_from_html(soup2)
            text = _norm_text(soup2.get_text(" "))
        return (title, text, dt)

# Chunking i ranking
_WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9_]+", re.UNICODE)

def _tokenize(text: str) -> List[str]:
    return [t.lower() for t in _WORD_RE.findall(text or "")]

def _chunks(text: str, min_chars=AUTO_MIN_CHARS, max_chars=AUTO_MAX_CHARS, overlap=180) -> List[str]:
    if len(text) <= max_chars:
        return [text]
    parts: List[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        slice_ = text[start:end]
        m = re.search(r"(?s)^(.{" + str(max_chars - 300) + r"," + str(max_chars) + r"}[\.\!\?])", slice_)
        block = m.group(1) if m else slice_
        parts.append(block)
        start = start + len(block) - overlap
        if start <= 0 or start >= len(text):
            break
    return [p for p in parts if len(p) >= min_chars or (len(parts) == 1 and len(p) > 0)]

class BM25:
    def __init__(self, corpus_tokens: List[List[str]], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = corpus_tokens
        self.N = len(corpus_tokens)
        self.df = Counter()
        self.avgdl = 1.0
        self._build()

    def _build(self):
        lengths = []
        for doc in self.docs:
            unique_terms = set(doc)
            for t in unique_terms:
                self.df[t] += 1
            lengths.append(len(doc))
        self.avgdl = sum(lengths) / max(1, len(lengths))

    def score(self, q: List[str], doc: List[str]) -> float:
        f = Counter(doc)
        dl = len(doc)
        sc = 0.0
        for term in q:
            n_qi = self.df.get(term, 0)
            if n_qi == 0:
                continue
            idf = math.log(1 + (self.N - n_qi + 0.5) / (n_qi + 0.5))
            freq = f.get(term, 0)
            denom = freq + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
            sc += idf * (freq * (self.k1 + 1)) / max(1e-9, denom)
        return sc

def _cosine_hash(q_tokens: List[str], d_tokens: List[str]) -> float:
    qset, dset = set(q_tokens), set(d_tokens)
    inter = len(qset & dset)
    denom = math.sqrt(len(qset) * len(dset)) or 1.0
    return inter / denom

def _jaccard(q_tokens: List[str], d_tokens: List[str]) -> float:
    qset, dset = set(q_tokens), set(d_tokens)
    if not qset or not dset:
        return 0.0
    return len(qset & dset) / len(qset | dset)

def _hybrid_rank(query: str, chunks: List[str]) -> List[Tuple[int, float]]:
    q_tokens = _tokenize(query)
    c_tokens = [_tokenize(c) for c in chunks]
    bm25 = BM25(c_tokens)
    scores = []
    for i, dtok in enumerate(c_tokens):
        s = 0.50 * bm25.score(q_tokens, dtok) + 0.35 * _cosine_hash(q_tokens, dtok) + 0.15 * _jaccard(q_tokens, dtok)
        scores.append((i, s))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores

# Ocena wiarygodności
_TRUST_DOMAINS = {
    "wikipedia.org": 0.9,
    "arxiv.org": 0.85,
    "semanticscholar.org": 0.8,
    "nature.com": 0.9,
    "science.org": 0.9,
    "acm.org": 0.85,
    "ieee.org": 0.85,
    "gov": 0.9,
    "edu": 0.85,
}

def _trust(url: str, https_ok: bool = True) -> float:
    d = _domain(url)
    sc = 0.6
    if https_ok and url.lower().startswith("https"):
        sc += 0.05
    if d.endswith(".gov") or d.endswith(".gov.pl"):
        sc = max(sc, 0.9)
    if d.endswith(".edu"):
        sc = max(sc, 0.85)
    for k, v in _TRUST_DOMAINS.items():
        if d.endswith(k):
            sc = max(sc, v)
    return min(sc, 0.98)

# LLM dla ekstrakcji faktów
_FACT_SYS = "Extract concise factual statements with explicit source URLs in strict JSON. Output JSON array of objects: [{\"fact\": str, \"source\": str}]. No prose."

def _fallback_fact_extract(prompt: str) -> str:
    facts = []
    for line in (prompt or "").splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.search(r"(https?://\S+)", line)
        if m:
            url = m.group(1)
            fact = _normalize_ws(line.replace(url, "")).strip(" -:—")
            if len(fact) >= 30:
                facts.append({"fact": fact, "source": url})
    return json.dumps(facts[:8], ensure_ascii=False)

def _llm_chat(system: str, user: str, maxtok: int = 1024, temp: float = 0.2) -> str:
    if not LLM_BASE_URL or not LLM_API_KEY:
        return _fallback_fact_extract(user)
    headers = {"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "max_tokens": maxtok,
        "temperature": temp,
    }
    try:
        resp = httpx.post(LLM_BASE_URL.rstrip("/") + "/chat/completions", json=payload, headers=headers, timeout=WEB_HTTP_TIMEOUT)
        resp.raise_for_status()
        js = resp.json()
        return js["choices"][0]["message"]["content"]
    except Exception:
        return _fallback_fact_extract(user)

def _llm_extract_facts(query: str, materials: List[Tuple[str, str, str]]) -> List[Tuple[str, str]]:
    lines = [f"Q: {query}"]
    for (u, t, txt) in materials:
        snippet = _normalize_ws(txt[:900])
        lines.append(f"- {t} [{u}] :: {snippet}")
    user_prompt = "\n".join(lines)
    raw = _llm_chat(_FACT_SYS, user_prompt, maxtok=800, temp=0.1)
    facts = []
    with contextlib.suppress(Exception):
        data = json.loads(raw)
        if isinstance(data, list):
            for it in data:
                fact = _norm_text(it.get("fact", ""))
                src = it.get("source")
                if fact and src and len(fact) >= 30:
                    facts.append((fact, _canonical_url(src)))
    if not facts:
        for (u, t, txt) in materials:
            sentences = re.split(r"(?<=[\.\!\?])\s+", txt)
            for s in sentences:
                s = _norm_text(s)
                if 60 <= len(s) <= 300 and s.lower() not in ("copyright", "all rights reserved"):
                    facts.append((s, _canonical_url(u)))
                    if len(facts) >= 6:
                        break
            if len(facts) >= 6:
                break
    return facts[:12]

# Pipeline główny
async def _ingest_url(query: str, title: str, url: str, topk_chunks: int = 2) -> Optional[Tuple[Material, List[Tuple[str, str]]]]:
    url_c = _canonical_url(url)
    https_ok = url_c.startswith("https")
    fetched = await _http_text(url_c)
    if not fetched:
        txt = await _firecrawl(url_c)
        if not txt:
            return None
        title2 = title or ""
        dt = None
        text = txt
    else:
        title2, text, dt = fetched
    if not text or len(text) < 200:
        return None
    parts = _chunks(text)
    ranked = _hybrid_rank(query, parts)[:topk_chunks]
    picked = " ".join(parts[i] for i, _ in ranked)
    dom = _domain(url_c)
    trust = _trust(url_c, https_ok)
    recency = _recency_score(dt)
    facts = _llm_extract_facts(query, [(url_c, title2 or title or "", picked)])
    material = Material(
        title=title2 or title or None,
        url=url_c,
        domain=dom,
        trust=trust,
        recency=recency,
        snippet=_norm_text(picked[:600]),
        facts=[f for f, _ in facts] if facts else [],
    )
    return material, facts

async def _gather_with_limit(coros: List, limit: int) -> List[Any]:
    sem = asyncio.Semaphore(limit)
    async def _run(c):
        async with sem:
            return await c
    return await asyncio.gather(*[_run(c) for c in coros], return_exceptions=True)

async def _search_all(query: str, mode: str) -> List[Tuple[str, str]]:
    tasks = []
    if mode in ("full", "grounded", "fast", "free"):
        tasks += [_ddg_search(query, AUTO_TOPK), _wiki_search(query, min(5, AUTO_TOPK))]
    if mode in ("full", "grounded"):
        tasks += [_s2_search(query, min(5, AUTO_TOPK)), _arxiv_search(query, min(5, AUTO_TOPK))]
        if SERPAPI_KEY:
            tasks.append(_serpapi_search(query, AUTO_TOPK))
    results: List[Tuple[str, str]] = []
    for out in await _gather_with_limit(tasks, limit=4):
        if not isinstance(out, Exception):
            results.extend(out or [])
    bydom: Dict[str, int] = defaultdict(int)
    filtered = []
    for (t, u) in results:
        d = _domain(u)
        if bydom[d] >= AUTON_DOMAIN_MAX:
            continue
        bydom[d] += 1
        filtered.append((t, u))
    return filtered[:max(AUTO_TOPK, 6)]

async def _pipeline(query: str, mode: str) -> Tuple[List[Material], List[Tuple[str, str]]]:
    pairs = await _search_all(query, mode)

    max_fetch = {
        "fast": min(3, AUTO_FETCH),
        "free": min(4, AUTO_FETCH),
        "grounded": max(4, AUTO_FETCH),
        "full": max(5, AUTO_FETCH)
    }.get(mode, AUTO_FETCH)

    fetch_tasks = []
    domain_counter = Counter()

    for t, u in pairs:
        domain = _domain(u)
        if domain_counter[domain] < AUTON_DOMAIN_MAX:
            domain_counter[domain] += 1
            fetch_tasks.append(_ingest_url(query, t, u))
            if len(fetch_tasks) >= max_fetch * 2:
                break

    outs = await _gather_with_limit(fetch_tasks[:max_fetch], limit=CONCURRENCY)
    materials: List[Material] = []
    facts_all: List[Tuple[str, str]] = []

    for out in outs:
        if isinstance(out, Exception) or out is None:
            continue
        m, facts = out

        if m and (not m.facts or len(m.facts) == 0) and m.snippet and len(m.snippet) > 300:
            additional_facts = _llm_extract_facts(query, [(m.url or "", m.title or "", m.snippet or "")])
            if additional_facts:
                m.facts = [f for f, _ in additional_facts]
                facts_all.extend(additional_facts)

        materials.append(m)
        facts_all.extend(facts)

    return materials, facts_all

def _dedup_key(fact: str, url: str) -> str:
    base = f"{_norm_text(fact).lower()}|{_domain(url)}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()

def _vote_and_store(facts: List[Tuple[str, str]], prof: Dict[str, dict]) -> Tuple[List[str], List[str]]:
    by_fact: Dict[str, set] = defaultdict(set)
    for fact, url in facts:
        by_fact[_norm_text(fact)].add(_domain(url))
    dedup = _LRUDedup(AUTON_DEDUP_MAX)
    ltm_ids: List[str] = []
    citations: List[str] = []
    for fact_norm, domains in by_fact.items():
        if len(domains) < VOTE_MIN_SOURCES:
            if not any(_trust(f"https://{d}") >= 0.85 for d in domains):
                continue
        src_dom = next(iter(domains))
        src_url = f"https://{src_dom}"
        key = _dedup_key(fact_norm, src_url)
        if dedup.has(key):
            continue
        dedup.put(key)
        meta = {"source_domains": list(domains), "source_url": src_url, "ts": _now_ts()}
        tags = [t.strip() for t in AUTO_TAGS.split(",") if t.strip()]
        fid = ltm_add(fact_norm, tags=tags, conf=0.9)
        ltm_ids.append(fid)
        citations.append(src_url)
    return ltm_ids, citations

def _llm_draft(query: str, materials: List[Material]) -> str:
    if not materials:
        return ""
    bullets = []
    for m in materials[:6]:
        if not m or not m.url:
            continue
        bullets.append(f"- [{m.title or m.url}]({_canonical_url(m.url)}) trust={m.trust:.2f if m.trust else 0.0} recency={m.recency:.2f if m.recency else 0.0}")
    pre = f"Query: {query}\nMaterials:\n" + "\n".join(bullets) + "\n\nSynthesis:\n"
    return _llm_chat("Write a concise, source-grounded synthesis. 5–8 bullet points. No fluff.", pre, maxtok=700, temp=0.2)

async def _web_learn_async(query: str, mode: str) -> LearnResult:
    materials, facts = await _pipeline(query, mode)
    ltm_ids, citations = _vote_and_store(facts, {})
    draft = _llm_draft(query, materials)
    trust_avg = float(sum(m.trust or 0 for m in materials) / max(1, len(materials)))
    return LearnResult(
        query=query,
        count=len(materials),
        trust_avg=trust_avg,
        backend="async-httpx",
        ltm_ids=ltm_ids,
        citations=citations,
        materials=materials,
        draft=draft
    )

def _run_sync(coro):
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    finally:
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        except Exception:
            pass
        loop.close()

def web_learn(query: str, mode: str = "full", **kwargs) -> Dict[str, Any]:
    if mode not in ("full", "fast", "free", "grounded"):
        mode = "full"

    try:
        res: LearnResult = _run_sync(_web_learn_async(query, mode))
        return {
            "query": res.query,
            "count": res.count,
            "trust_avg": res.trust_avg,
            "backend": res.backend,
            "ltm_ids": res.ltm_ids,
            "citations": res.citations,
            "materials": [dataclasses.asdict(m) for m in res.materials],
            "draft": res.draft,
        }
    except Exception as e:
        return {
            "query": query,
            "count": 0,
            "trust_avg": 0.0,
            "backend": "fallback",
            "ltm_ids": [],
            "citations": [],
            "materials": [],
            "draft": f"Błąd podczas wyszukiwania informacji o '{query}': {str(e)}",
        }

# Funkcje dla newsów sportowych
async def news_search(query: str = "top", limit: int = 6) -> Dict[str, Any]:
    """Wyszukiwanie aktualności sportowych"""
    try:
        if not SERPAPI_KEY:
            return {"ok": False, "error": "SERPAPI_KEY missing"}

        api = "https://serpapi.com/search.json"
        params = {
            "engine": "google_news",
            "q": query,
            "num": str(limit),
            "api_key": SERPAPI_KEY
        }

        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            r = await client.get(api, params=params)
            if r.status_code >= 400:
                return {"ok": False, "error": f"API error: {r.status_code}"}

            js = r.json()
            items = []
            for it in js.get("news_results", [])[:limit]:
                items.append({
                    "title": it.get("title", ""),
                    "link": it.get("link", ""),
                    "date": it.get("date", ""),
                    "source": it.get("source", {}).get("name", "")
                })

            return {"ok": True, "items": items}

    except Exception as e:
        return {"ok": False, "error": str(e)}

def normalize_scores(kind: str = "nba", limit: int = 8) -> List[Dict[str, Any]]:
    """Normalizacja wyników sportowych z ESPN"""
    try:
        from urllib.request import urlopen
        from urllib.parse import Request, urlencode

        ESPN_URLS = {
            "nba": "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
            "nfl": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
            "mlb": "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard",
            "nhl": "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard",
            "soccer": "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard"
        }

        base = ESPN_URLS.get(kind.lower())
        if not base:
            return []

        j = httpx.get(base).json()
        events = j.get("events", [])
        out = []

        for e in events[:limit]:
            comp = (e.get("competitions") or [{}])[0]
            status = (comp.get("status") or {}).get("type", {})
            short = status.get("shortDetail") or status.get("name") or ""
            teams = (comp.get("competitors") or [])

            if len(teams) == 2:
                t1 = teams[0]
                t2 = teams[1]
                out.append({
                    "home": t1.get("team", {}).get("displayName"),
                    "home_score": t1.get("score"),
                    "away": t2.get("team", {}).get("displayName"),
                    "away_score": t2.get("score"),
                    "status": short,
                    "venue": (comp.get("venue") or {}).get("fullName"),
                    "start": e.get("date"),
                    "kind": kind.upper()
                })

        return out

    except Exception:
        return []