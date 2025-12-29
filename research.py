#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Research Module - autonauka, web_learn, web scraping
FULL LOGIC - NO PLACEHOLDERS!
"""
import os, re, sys, time, json, uuid, asyncio, contextlib, hashlib, dataclasses, math
import datetime
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple, Optional
from urllib.parse import quote_plus, urlparse, urlencode, parse_qsl, urlunparse
from collections import Counter, defaultdict
from dataclasses import dataclass
import html as html_lib, unicodedata

import httpx
from bs4 import BeautifulSoup
from readability import Document as ReadabilityDoc

from .config import (
    SERPAPI_KEY, FIRECRAWL_API_KEY, BASE_DIR, DB_PATH, HTTP_TIMEOUT,
    LLM_BASE_URL, LLM_API_KEY, LLM_MODEL
)
from .helpers import (
    log_info, log_warning, log_error, http_get_json,
    normalize_text as _norm, make_id as _id_for, tokenize as _tok,
    tfidf_cosine as _tfidf_cos, cosine_similarity as _vec_cos
)
from .memory import _db, ltm_add, cache_get, cache_put
from .llm import call_llm

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

WEB_HTTP_TIMEOUT = float(os.getenv("WEB_HTTP_TIMEOUT", "45"))
AUTO_TOPK = int(os.getenv("AUTO_TOPK", "8"))
AUTO_FETCH = int(os.getenv("AUTO_FETCH", "4"))
AUTO_MIN_CHARS = int(os.getenv("AUTO_MIN_CHARS", "800"))
AUTO_MAX_CHARS = int(os.getenv("AUTO_MAX_CHARS", "8000"))
AUTON_DEDUP_MAX = int(os.getenv("AUTON_DEDUP_MAX", "1000"))
AUTON_DOMAIN_MAX = int(os.getenv("AUTON_DOMAIN_MAX", "2"))
VOTE_MIN_SOURCES = int(os.getenv("VOTE_MIN_SOURCES", "2"))
AUTO_TAGS = os.getenv("AUTO_TAGS", "autonauka,web,evidence")
CONCURRENCY = int(os.getenv("AUTON_CONCURRENCY", "8"))
USER_AGENT = os.getenv("AUTON_UA", "Autonauka/1.0")
FIRECRAWL_KEY = FIRECRAWL_API_KEY
OPENTRIPMAP_KEY = os.getenv("OTM_API_KEY", "")
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# ═══════════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════════

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

# ═══════════════════════════════════════════════════════════════════
# TEXT UTILITIES
# ═══════════════════════════════════════════════════════════════════

_WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9_]+", re.UNICODE)

def _tokenize(text: str) -> List[str]:
    return [t.lower() for t in _WORD_RE.findall(text or "")]

def _normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()

def _norm_text(s: str) -> str:
    s = html_lib.unescape(s or "")
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\u200b", "")
    return _normalize_ws(s)

_CANON_SKIP_PARAMS = {"utm_source","utm_medium","utm_campaign","utm_term","utm_content","gclid","fbclid","igshid","mc_cid","mc_eid"}

def _canonical_url(url: str) -> str:
    try:
        p = urlparse(url)
        scheme = "https" if p.scheme in ("http","https") else p.scheme
        query = urlencode([(k,v) for k,v in parse_qsl(p.query, keep_blank_values=True) if k not in _CANON_SKIP_PARAMS])
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

def _chunks(text: str, min_chars=AUTO_MIN_CHARS, max_chars=AUTO_MAX_CHARS, overlap=180) -> List[str]:
    if len(text) <= max_chars:
        return [text]
    parts: List[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        slice_ = text[start:end]
        m = re.search(r"(?s)^(.{"+str(max_chars - 300)+r"," + str(max_chars) + r"}[\.\!\?])", slice_)
        block = m.group(1) if m else slice_
        parts.append(block)
        start = start + len(block) - overlap
        if start <= 0 or start >= len(text): break
    return [p for p in parts if len(p) >= min_chars or (len(parts)==1 and len(p)>0)]

def chunk_text(text: str, max_words: int = 240, overlap: int = 60) -> List[str]:
    words=text.split(); out=[]; i=0; step=max_words-overlap; step=step if step>0 else max_words
    while i<len(words):
        out.append(" ".join(words[i:i+max_words])); i+=step
    return out

# ═══════════════════════════════════════════════════════════════════
# DATE PARSING
# ═══════════════════════════════════════════════════════════════════

def _parse_date_from_html(soup: BeautifulSoup) -> Optional[datetime]:
    for sel,attr in [
        ('meta[property="article:published_time"]',"content"),
        ('meta[name="pubdate"]',"content"),
        ('meta[name="date"]',"content"),
        ('time[datetime]',"datetime"),
        ('meta[itemprop="datePublished"]',"content"),
    ]:
        tag = soup.select_one(sel)
        if tag and tag.get(attr):
            with contextlib.suppress(Exception):
                return datetime.fromisoformat(tag.get(attr).replace("Z","+00:00"))
    text = soup.get_text(" ", strip=True)
    m = re.search(r"(20\d{2}[-/\.]\d{1,2}[-/\.]\d{1,2})", text)
    if m:
        s = m.group(1).replace("/", "-").replace(".", "-")
        y,mn,dd = map(int, s.split("-"))
        with contextlib.suppress(Exception):
            return datetime(y,mn,dd,tzinfo=timezone.utc)
    return None

def _recency_score(dt: Optional[datetime]) -> float:
    if not dt:
        return 0.3
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=timezone.utc)
    days = max(1.0, (datetime.now(timezone.utc) - dt).total_seconds()/86400.0)
    return max(0.2, 1.0 / math.log2(2+days/7))

# ═══════════════════════════════════════════════════════════════════
# HTTP CLIENT
# ═══════════════════════════════════════════════════════════════════

def _client() -> httpx.AsyncClient:
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/json;q=0.9,*/*;q=0.8"}
    return httpx.AsyncClient(follow_redirects=True, timeout=WEB_HTTP_TIMEOUT, headers=headers)

# ═══════════════════════════════════════════════════════════════════
# SEARCH FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

async def _ddg_search(q: str, k: int) -> List[Tuple[str,str]]:
    url = "https://duckduckgo.com/html/"
    out: List[Tuple[str,str]] = []
    async with _client() as cl:
        r = await cl.post(url, data={"q": q})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.select("a.result__a"):
            href = a.get("href"); title = _norm_text(a.text)
            if href and title:
                out.append((title, href))
            if len(out)>=k: break
    return out

async def _wiki_search(q: str, k: int) -> List[Tuple[str,str]]:
    api = "https://en.wikipedia.org/w/api.php"
    params = {"action":"opensearch","format":"json","limit":str(k),"search":q}
    async with _client() as cl:
        r = await cl.get(api, params=params)
        r.raise_for_status()
        js = r.json()
    return [(_norm_text(t), l) for t,l in zip(js[1], js[3])]

async def _arxiv_search(q: str, k: int) -> List[Tuple[str,str]]:
    api = "http://export.arxiv.org/api/query"
    params = {"search_query": q, "start":"0", "max_results": str(k)}
    async with _client() as cl:
        r = await cl.get(api, params=params)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "xml")
    out=[]
    for e in soup.select("entry"):
        t = _norm_text(e.select_one("title").text if e.select_one("title") else "")
        link = e.select_one("id").text if e.select_one("id") else None
        if t and link: out.append((t, link))
    return out[:k]

async def _s2_search(q: str, k: int) -> List[Tuple[str,str]]:
    api = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {"query": q, "limit": str(k), "fields":"title,url"}
    async with _client() as cl:
        r = await cl.get(api, params=params)
        if r.status_code >= 400: return []
        js = r.json()
    out=[]
    for it in js.get("data", []):
        t = _norm_text(it.get("title") or ""); u = it.get("url")
        if t and u: out.append((t,u))
    return out

async def _serpapi_search(q: str, k: int) -> List[Tuple[str,str]]:
    if not SERPAPI_KEY: return []
    api = "https://serpapi.com/search.json"
    params = {"engine":"google","q":q,"num":str(k),"api_key":SERPAPI_KEY}
    async with _client() as cl:
        r = await cl.get(api, params=params)
        if r.status_code >= 400: return []
        js = r.json()
    out=[]
    for it in js.get("organic_results", []):
        t=_norm_text(it.get("title","")); u=it.get("link")
        if t and u: out.append((t,u))
    return out[:k]

async def _search_all(query: str, mode: str) -> List[Tuple[str,str]]:
    tasks = []
    if mode in ("full","grounded","fast","free"):
        tasks += [_ddg_search(query, AUTO_TOPK), _wiki_search(query, min(5, AUTO_TOPK))]
    if mode in ("full","grounded"):
        tasks += [_s2_search(query, min(5, AUTO_TOPK)), _arxiv_search(query, min(5, AUTO_TOPK))]
        if SERPAPI_KEY: tasks.append(_serpapi_search(query, AUTO_TOPK))
    results: List[Tuple[str,str]] = []
    for out in await _gather_with_limit(tasks, limit=4):
        if not isinstance(out, Exception): results.extend(out or [])
    bydom: Dict[str, int] = defaultdict(int); filtered=[]
    for (t,u) in results:
        d=_domain(u)
        if bydom[d] >= AUTON_DOMAIN_MAX: continue
        bydom[d]+=1; filtered.append((t,u))
    return filtered[:max(AUTO_TOPK, 6)]

# ═══════════════════════════════════════════════════════════════════
# SCRAPING
# ═══════════════════════════════════════════════════════════════════

async def _firecrawl(url: str) -> Optional[str]:
    if not FIRECRAWL_KEY:
        return None
    api = "https://api.firecrawl.dev/v1/scrape"
    payload = {"url": url, "formats":["markdown","html","rawHtml"], "actions":[]}
    headers = {"Authorization": f"Bearer {FIRECRAWL_KEY}", "Content-Type":"application/json"}
    async with _client() as cl:
        r = await cl.post(api, json=payload, headers=headers)
        if r.status_code >= 400:
            return None
        js = r.json()
    text = js.get("markdown") or js.get("html") or js.get("rawHtml")
    if not text: return None
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

def extract_text(html: str) -> Tuple[str, str]:
    try:
        doc = ReadabilityDoc(html)
        title = doc.short_title()
        soup = BeautifulSoup(doc.summary(html_partial=True), "html.parser")
        return title, soup.get_text(" ", strip=True)
    except Exception:
        txt=re.sub(r"\s+"," ", re.sub(r"<.*?>"," ", html))
        return "", txt.strip()

# ═══════════════════════════════════════════════════════════════════
# BM25 RANKING
# ═══════════════════════════════════════════════════════════════════

class BM25:
    def __init__(self, corpus_tokens: List[List[str]], k1: float=1.5, b: float=0.75):
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
                self.df[t]+=1
            lengths.append(len(doc))
        self.avgdl = sum(lengths)/max(1,len(lengths))
    def score(self, q: List[str], doc: List[str]) -> float:
        f = Counter(doc); dl = len(doc); sc = 0.0
        for term in q:
            n_qi = self.df.get(term,0)
            if n_qi==0: continue
            idf = math.log(1 + (self.N - n_qi + 0.5)/(n_qi + 0.5))
            freq = f.get(term,0)
            denom = freq + self.k1*(1 - self.b + self.b*dl/self.avgdl)
            sc += idf * (freq*(self.k1+1))/max(1e-9, denom)
        return sc

def _cosine_hash(q_tokens: List[str], d_tokens: List[str]) -> float:
    qset, dset = set(q_tokens), set(d_tokens)
    inter = len(qset & dset)
    denom = math.sqrt(len(qset)*len(dset)) or 1.0
    return inter/denom

def _jaccard(q_tokens: List[str], d_tokens: List[str]) -> float:
    qset, dset = set(q_tokens), set(d_tokens)
    if not qset or not dset: return 0.0
    return len(qset & dset)/len(qset | dset)

def _hybrid_rank(query: str, chunks: List[str]) -> List[Tuple[int,float]]:
    q_tokens = _tokenize(query)
    c_tokens = [_tokenize(c) for c in chunks]
    bm25 = BM25(c_tokens)
    scores = []
    for i, dtok in enumerate(c_tokens):
        s = 0.50*bm25.score(q_tokens, dtok) + 0.35*_cosine_hash(q_tokens, dtok) + 0.15*_jaccard(q_tokens, dtok)
        scores.append((i, s))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores

def rank_hybrid(chunks: List[str], q: str, topk: int = 6) -> List[Tuple[str,float]]:
    if not chunks: return []
    tfidf=_tfidf_cos(q, chunks)
    emb=[0.0]*len(chunks)
    from .helpers import embed_many
    try:
        qv=embed_many([q]); ev=embed_many(chunks)
        if qv and ev:
            qv=qv[0]; emb=[_vec_cos(qv,e) for e in ev]
    except Exception: pass
    out=[]
    for i,ch in enumerate(chunks):
        score=0.58*(tfidf[i] if i<len(tfidf) else 0.0) + 0.42*(emb[i] if i<len(emb) else 0.0)
        out.append((ch,float(score)))
    out.sort(key=lambda x:x[1], reverse=True)
    return out[:topk]

# ═══════════════════════════════════════════════════════════════════
# TRUST & REPUTATION
# ═══════════════════════════════════════════════════════════════════

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
def _trust(url: str, https_ok: bool=True) -> float:
    d = _domain(url); sc = 0.6
    if https_ok and url.lower().startswith("https"): sc += 0.05
    if d.endswith(".gov") or d.endswith(".gov.pl"): sc = max(sc, 0.9)
    if d.endswith(".edu"): sc = max(sc, 0.85)
    for k,v in _TRUST_DOMAINS.items():
        if d.endswith(k): sc = max(sc, v)
    return min(sc, 0.98)

# ═══════════════════════════════════════════════════════════════════
# LLM FACT EXTRACTION
# ═══════════════════════════════════════════════════════════════════

_FACT_SYS = "Extract concise factual statements with explicit source URLs in strict JSON. Output JSON array of objects: [{\"fact\": str, \"source\": str}]. No prose."

def _fallback_fact_extract(prompt: str) -> str:
    facts=[]
    for line in (prompt or "").splitlines():
        line=line.strip()
        if not line: continue
        m = re.search(r"(https?://\S+)", line)
        if m:
            url = m.group(1)
            fact = _normalize_ws(line.replace(url,"")).strip(" -:—")
            if len(fact)>=30:
                facts.append({"fact": fact, "source": url})
    return json.dumps(facts[:8], ensure_ascii=False)

def _llm_chat(system: str, user: str, maxtok: int=1024, temp: float=0.2) -> str:
    if not LLM_BASE_URL or not LLM_API_KEY:
        return _fallback_fact_extract(user)
    headers = {"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type":"application/json"}
    payload = {
        "model": LLM_MODEL,
        "messages": [{"role":"system","content":system},{"role":"user","content":user}],
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

def _llm_extract_facts(query: str, materials: List[Tuple[str,str,str]]) -> List[Tuple[str,str]]:
    lines = [f"Q: {query}"]
    for (u,t,txt) in materials:
        snippet = _normalize_ws(txt[:900])
        lines.append(f"- {t} [{u}] :: {snippet}")
    user_prompt = "\n".join(lines)
    raw = _llm_chat(_FACT_SYS, user_prompt, maxtok=800, temp=0.1)
    facts=[]
    with contextlib.suppress(Exception):
        data = json.loads(raw)
        if isinstance(data, list):
            for it in data:
                fact = _norm_text(it.get("fact",""))
                src = it.get("source")
                if fact and src and len(fact)>=30:
                    facts.append((fact, _canonical_url(src)))
    if not facts:
        for (u, t, txt) in materials:
            sentences = re.split(r"(?<=[\.\!\?])\s+", txt)
            for s in sentences:
                s=_norm_text(s)
                if 60 <= len(s) <= 300 and s.lower() not in ("copyright","all rights reserved"):
                    facts.append((s, _canonical_url(u)))
                    if len(facts)>=6: break
            if len(facts)>=6: break
    return facts[:12]

# ═══════════════════════════════════════════════════════════════════
# URL INGESTION
# ═══════════════════════════════════════════════════════════════════

async def _ingest_url(query: str, title: str, url: str, topk_chunks: int = 2) -> Optional[Tuple[Material, List[Tuple[str,str]]]]:
    url_c = _canonical_url(url)
    https_ok = url_c.startswith("https")
    fetched = await _http_text(url_c)
    if not fetched:
        txt = await _firecrawl(url_c)
        if not txt: return None
        title2 = title or ""
        dt = None; text = txt
    else:
        title2, text, dt = fetched
    if not text or len(text) < 200: return None
    parts = _chunks(text)
    ranked = _hybrid_rank(query, parts)[:topk_chunks]
    picked = " ".join(parts[i] for i,_ in ranked)
    dom = _domain(url_c)
    trust = _trust(url_c, https_ok)
    recency = _recency_score(dt)
    facts = _llm_extract_facts(query, [(url_c, title2 or title or "", picked)])
    material = Material(
        title=title2 or title or None,
        url=url_c, domain=dom, trust=trust, recency=recency,
        snippet=_norm_text(picked[:600]),
        facts=[f for f,_ in facts] if facts else [],
    )
    return material, facts

# ═══════════════════════════════════════════════════════════════════
# DEDUPLICATION
# ═══════════════════════════════════════════════════════════════════

class _LRUDedup:
    def __init__(self, cap: int):
        self.cap = cap; self.order: List[str] = []; self.set = set()
    def put(self, key: str) -> None:
        if key in self.set:
            with contextlib.suppress(ValueError): self.order.remove(key)
            self.order.append(key); return
        self.set.add(key); self.order.append(key)
        if len(self.order) > self.cap:
            old = self.order.pop(0); self.set.discard(old)
    def has(self, key: str) -> bool:
        return key in self.set

def _dedup_key(fact: str, url: str) -> str:
    base = f"{_norm_text(fact).lower()}|{_domain(url)}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()

# ═══════════════════════════════════════════════════════════════════
# ASYNC UTILS
# ═══════════════════════════════════════════════════════════════════

async def _gather_with_limit(coros: List, limit: int) -> List[Any]:
    sem = asyncio.Semaphore(limit)
    async def _run(c):
        async with sem: return await c
    return await asyncio.gather(*[_run(c) for c in coros], return_exceptions=True)

# ═══════════════════════════════════════════════════════════════════
# PIPELINE
# ═══════════════════════════════════════════════════════════════════

async def _pipeline(query: str, mode: str) -> Tuple[List[Material], List[Tuple[str,str]]]:
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
    materials: List[Material] = []; facts_all: List[Tuple[str,str]] = []
    
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

# ═══════════════════════════════════════════════════════════════════
# VOTING & STORAGE
# ═══════════════════════════════════════════════════════════════════

class _NoopMemory:
    def add_fact(self, text: str, meta: Optional[dict] = None, tags: Optional[List[str]] = None) -> str:
        return f"noop-{hashlib.sha1(text.encode()).hexdigest()[:12]}"
    def get_profile(self, key: str) -> Optional[dict]:
        return None
    def set_profile_many(self, entries: Dict[str, dict]) -> None:
        pass

def _get_memory():
    return _NoopMemory()

MEM = _get_memory()
PROF_KEY = "web_domain_weights"

def _load_profile() -> Dict[str, dict]:
    prof = MEM.get_profile(PROF_KEY)
    return prof if isinstance(prof, dict) else {}

def _save_profile_many(prof: Dict[str, dict]) -> None:
    MEM.set_profile_many({PROF_KEY: prof})

def _bump_domain_weight(prof: Dict[str, dict], domain: str, success: bool) -> None:
    it = prof.get(domain) or {"w": 0.0, "n": 0}
    w = float(it.get("w",0.0)); n = int(it.get("n",0))
    w = w + (0.05 if success else -0.03)
    w = max(-0.5, min(0.8, w)); n += 1
    prof[domain] = {"w": w, "n": n}

def _domain_weight(prof: Dict[str, dict], domain: str) -> float:
    it = prof.get(domain); return float(it.get("w",0.0)) if it else 0.0

def _vote_and_store(facts: List[Tuple[str,str]], prof: Dict[str,dict]) -> Tuple[List[str], List[str]]:
    by_fact: Dict[str, set] = defaultdict(set)
    for fact, url in facts: by_fact[_norm_text(fact)].add(_domain(url))
    dedup = _LRUDedup(AUTON_DEDUP_MAX); ltm_ids: List[str] = []; citations: List[str] = []
    for fact_norm, domains in by_fact.items():
        if len(domains) < VOTE_MIN_SOURCES:
            if not any(_trust(f"https://{d}") >= 0.85 for d in domains): continue
        src_dom = next(iter(domains)); src_url = f"https://{src_dom}"
        key = _dedup_key(fact_norm, src_url)
        if dedup.has(key): continue
        dedup.put(key)
        tags = [t.strip() for t in AUTO_TAGS.split(",") if t.strip()]
        fid = ltm_add(fact_norm, tags=",".join(tags), conf=0.9)
        ltm_ids.append(fid); citations.append(src_url)
        for d in domains: _bump_domain_weight(prof, d, True)
    _save_profile_many(prof)
    return ltm_ids, citations

# ═══════════════════════════════════════════════════════════════════
# DRAFT GENERATION
# ═══════════════════════════════════════════════════════════════════

def _llm_draft(query: str, materials: List[Material]) -> str:
    if not materials: return ""
    bullets=[]
    for m in materials[:6]:
        if not m or not m.url: continue
        bullets.append(f"- [{m.title or m.url}]({_canonical_url(m.url)}) trust={m.trust:.2f if m.trust else 0.0} recency={m.recency:.2f if m.recency else 0.0}")
    pre = f"Query: {query}\nMaterials:\n" + "\n".join(bullets) + "\n\nSynthesis:\n"
    return _llm_chat("Write a concise, source-grounded synthesis. 5–8 bullet points. No fluff.", pre, maxtok=700, temp=0.2)

# ═══════════════════════════════════════════════════════════════════
# WEB LEARN
# ═══════════════════════════════════════════════════════════════════

async def _web_learn_async(query: str, mode: str) -> LearnResult:
    prof = _load_profile()
    materials, facts = await _pipeline(query, mode)
    ltm_ids, citations = _vote_and_store(facts, prof)
    draft = _llm_draft(query, materials)
    trust_avg = float(sum(m.trust or 0 for m in materials)/max(1,len(materials)))
    return LearnResult(query=query,count=len(materials),trust_avg=trust_avg,backend="async-httpx",
                       ltm_ids=ltm_ids,citations=citations,materials=materials,draft=draft)

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

def web_learn(query: str, mode: str="full", **kwargs) -> Dict[str, Any]:
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
        log_error(e, "WEB_LEARN")
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

# ═══════════════════════════════════════════════════════════════════
# RESEARCH COLLECT (legacy)
# ═══════════════════════════════════════════════════════════════════

async def serpapi_search(q: str, engine: str = "google", params: dict = None) -> dict:
    if not SERPAPI_KEY: return {"ok": False, "error": "SERPAPI_KEY missing"}
    base = "https://serpapi.com/search.json"
    p = {"engine": engine, "q": q, "api_key": SERPAPI_KEY}
    if params: p.update(params)
    from .config import WEB_USER_AGENT
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, headers={"User-Agent":WEB_USER_AGENT}) as c:
        r = await c.get(base, params=p)
        try: return {"ok": r.status_code==200, "status": r.status_code, "data": r.json()}
        except: return {"ok": False, "raw": r.text}

async def firecrawl_scrape(url: str) -> dict:
    if not FIRECRAWL_KEY: return {"ok": False, "error": "FIRECRAWL_KEY missing"}
    endpoint = "https://api.firecrawl.dev/v1/scrape"
    headers = {"Authorization": f"Bearer {FIRECRAWL_KEY}"}
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as c:
        r = await c.post(endpoint, headers=headers, json={"url": url})
        try: return {"ok": r.status_code==200, "data": r.json()}
        except: return {"ok": False, "raw": r.text}

async def wiki_search(q: str, n: int = 5) -> List[str]:
    url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={quote_plus(q)}&utf8=&format=json&srlimit={n}"
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as c:
        r = await c.get(url); j = r.json()
        return [f"https://en.wikipedia.org/wiki/{quote_plus(p['title'])}" for p in j.get("query",{}).get("search",[])]

def store_docs(items: List[dict]):
    conn=_db(); c=conn.cursor()
    for it in items:
        did=uuid.uuid4().hex
        c.execute("INSERT OR REPLACE INTO docs VALUES(?,?,?,?,?,?)",(did,it.get("url",""),it.get("title",""),it.get("text",""),it.get("source","web"),time.time()))
        try: c.execute("INSERT INTO docs_fts(title,text,url) VALUES(?,?,?)",(it.get("title",""),it.get("text",""),it.get("url","")))
        except Exception: pass
    conn.commit(); conn.close()

async def research_collect(q: str, max_sites: int = 10) -> List[dict]:
    from .config import WEB_USER_AGENT
    links=[]
    if SERPAPI_KEY:
        s = await serpapi_search(q, "google", params={"num": max_sites})
        for o in (s.get("data",{}) or {}).get("organic_results", [])[:max_sites]:
            if o.get("link"): links.append(o["link"])
        sch = await serpapi_search(q, "google_scholar", params={"num":3})
        for o in (sch.get("data",{}) or {}).get("organic_results", [])[:3]:
            if o.get("link"): links.append(o["link"])
    links += await wiki_search(q, n=3)
    seen=set(); ulist=[]
    for u in links:
        if u and u not in seen: seen.add(u); ulist.append(u)
    out=[]
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, headers={"User-Agent":WEB_USER_AGENT}, follow_redirects=True) as c:
        res=await asyncio.gather(*[c.get(u) for u in ulist[:max_sites]], return_exceptions=True)
        for u, r in zip(ulist[:max_sites], res):
            if isinstance(r, Exception):
                if FIRECRAWL_KEY:
                    fr=await firecrawl_scrape(u)
                    if fr.get("ok") and fr.get("data") and fr["data"].get("content"):
                        out.append({"url":u,"title":fr["data"].get("title",""),"text":fr["data"]["content"],"source":"firecrawl"})
                continue
            html=r.text or ""
            if FIRECRAWL_KEY:
                fr=await firecrawl_scrape(u)
                if fr.get("ok") and fr["data"].get("content"):
                    out.append({"url":u,"title":fr["data"].get("title",""),"text":fr["data"]["content"],"source":"firecrawl"})
                    continue
            title, text = extract_text(html)
            out.append({"url":u,"title":title,"text":text,"source":"web"})
    return out

# ═══════════════════════════════════════════════════════════════════
# HIERARCHICAL MEMORY INTEGRATION
# ═══════════════════════════════════════════════════════════════════

try:
    from .hierarchical_memory import (
        enhance_memory_with_hierarchy,
        get_hierarchical_context,
        get_hierarchical_memory_system
    )
    HIERARCHICAL_MEMORY_AVAILABLE = True
    print("[OK] ✅ Hierarchical Memory integrated with Research Module!")
except ImportError as e:
    print(f"[WARN] Hierarchical Memory not available for Research: {e}")
    HIERARCHICAL_MEMORY_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════════
# AUTONAUKA MAIN FUNCTION - ENHANCED WITH HIERARCHICAL MEMORY
# ═══════════════════════════════════════════════════════════════════

async def autonauka(q: str, topk: int = 10, deep_research: bool = False, use_external_module: bool = True, user_id: str = None) -> dict:
    """
    Enhanced autonauka with Hierarchical Memory System integration.
    Now stores research results in L1-L4 levels and uses existing knowledge.
    """
    key=f"autonauka:{q}:{topk}:{deep_research}:{use_external_module}:{user_id or 'default'}"
    cach=cache_get(key, ttl=1800)
    if cach and isinstance(cach, dict) and "context" in cach and "sources" in cach:
        return cach
    
    # NEW: Check hierarchical memory first for existing knowledge
    hierarchical_context = {}
    if HIERARCHICAL_MEMORY_AVAILABLE:
        try:
            print(f"🧠 Checking hierarchical memory for: '{q[:60]}...'")
            hierarchical_context = get_hierarchical_context(q, user_id, max_size=2000)
            
            # If we have high-confidence context from hierarchical memory, use it
            if (hierarchical_context.get('total_confidence', 0) > 0.7 and 
                len(hierarchical_context.get('semantic_facts', [])) >= 3):
                
                print(f"🧠 Using existing hierarchical knowledge (confidence: {hierarchical_context.get('total_confidence', 0):.2f})")
                
                # Build context from hierarchical memory
                ctx_parts = []
                facts_list = []
                sources_list = []
                
                # Add semantic facts (L2)
                for fact in hierarchical_context.get('semantic_facts', [])[:topk]:
                    ctx_parts.append(fact.get('text', ''))
                    facts_list.append(fact.get('text', ''))
                
                # Add episodic memories (L1) 
                for episode in hierarchical_context.get('episodic_memories', [])[:3]:
                    ctx_parts.append(episode.get('summary', ''))
                
                # Create sources from facts
                for i, fact in enumerate(hierarchical_context.get('semantic_facts', [])[:5]):
                    sources_list.append({
                        "title": f"Hierarchical Memory Fact {i+1}",
                        "url": f"hierarchical://L2/fact/{fact.get('id', 'unknown')}",
                        "source_type": "hierarchical_memory"
                    })
                
                hierarchical_result = {
                    "query": q,
                    "context": "\n\n".join(ctx_parts[:topk]),
                    "facts": facts_list[:5],
                    "sources": sources_list,
                    "is_deep_research": deep_research,
                    "source_count": len(hierarchical_context.get('semantic_facts', [])),
                    "powered_by": "hierarchical-memory-system",
                    "hierarchical_confidence": hierarchical_context.get('total_confidence', 0),
                    "cache_hit": False
                }
                
                cache_put(key, hierarchical_result)
                return hierarchical_result
                
        except Exception as e:
            print(f"[WARN] Hierarchical memory check failed: {e}")
    
    try:
        # Użyj async wersji zamiast sync _run_sync
        result_obj = await _web_learn_async(q, mode="full" if deep_research else "fast")
        
        # Konwertuj LearnResult na dict
        result = {
            "query": result_obj.query,
            "count": result_obj.count,
            "trust_avg": result_obj.trust_avg,
            "backend": result_obj.backend,
            "ltm_ids": result_obj.ltm_ids,
            "citations": result_obj.citations,
            "materials": [dataclasses.asdict(m) for m in result_obj.materials],
            "draft": result_obj.draft,
        }
        
        if result and isinstance(result, dict) and "materials" in result:
            ctx = []
            cites = []
            fact_highlights = []
            
            for mat in result.get("materials", []):
                if not isinstance(mat, dict): continue
                facts = mat.get("facts", [])
                for fact in facts:
                    if fact and len(fact) > 40:
                        ctx.append(fact)
                url = mat.get("url", "")
                title = mat.get("title", "")
                if url:
                    cites.append({"title": title or url, "url": url})
            
            if result.get("draft"):
                draft_parts = result["draft"].split("\n")
                for part in draft_parts:
                    if part.startswith("- ") and len(part) > 30:
                        fact_highlights.append(part[2:])
            
            out = {
                "query": q,
                "context": "\n\n".join(ctx[:topk]),
                "facts": fact_highlights[:5],
                "sources": cites[:max(12, topk)],
                "is_deep_research": deep_research,
                "source_count": len(result.get("materials", [])),
                "powered_by": "autonauka-module"
            }
            
            # NEW: Store research results in hierarchical memory
            if HIERARCHICAL_MEMORY_AVAILABLE and user_id:
                try:
                    research_context = {
                        "research_query": q,
                        "deep_research": deep_research,
                        "source_count": out["source_count"],
                        "timestamp": time.time(),
                        "research_type": "web_autonauka"
                    }
                    
                    research_summary = f"Autonauka: {q} - znaleziono {out['source_count']} źródeł"
                    if deep_research:
                        research_summary += " (głębokie badanie)"
                    
                    memory_result = enhance_memory_with_hierarchy(research_summary, research_context, user_id)
                    print(f"🧠 Zapisano wyniki autonauki w pamięci hierarchicznej: {memory_result.get('episode_id', 'unknown')}")
                    
                    out["hierarchical_memory"] = {
                        "stored": True,
                        "episode_id": memory_result.get("episode_id"),
                        "semantic_updates": len(memory_result.get("semantic_updates", [])),
                        "procedural_updates": len(memory_result.get("procedural_updates", []))
                    }
                    
                except Exception as e:
                    print(f"[WARN] Failed to store in hierarchical memory: {e}")
                    out["hierarchical_memory"] = {"stored": False, "error": str(e)}
            
            cache_put(key, out)
            return out
    except Exception as e:
        log_error(e, "AUTONAUKA_WEB_LEARN")
    
    # Fallback - built-in implementation
    from .memory import ltm_search_hybrid
    
    expanded_variants = [q]
    if deep_research:
        current_year = datetime.now().year
        expanded_variants.extend([
            f"{q} najlepsze praktyki",
            f"{q} przykłady",
            f"{q} trendy {current_year}",
            f"{q} praktyczne zastosowania",
            f"{q} zaawansowane techniki"
        ])
    
    all_items = []
    tasks = [research_collect(variant, max_sites=8 if deep_research else 6) for variant in expanded_variants]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for res in results:
        if isinstance(res, Exception):
            continue
        all_items.extend(res)
    
    seen_urls = set()
    seen_domains = {}
    items = []
    
    for item in all_items:
        url = item.get("url", "")
        if not url:
            continue
        domain = _domain(url)
        
        if url not in seen_urls:
            if domain in seen_domains:
                if seen_domains[domain] >= (3 if deep_research else 2):
                    continue
                seen_domains[domain] += 1
            else:
                seen_domains[domain] = 1
            
            seen_urls.add(url)
            items.append(item)
    
    items = items[:20 if deep_research else 15]
    
    if not items:
        fallback_items = await research_collect(q.split()[-1] if len(q.split()) > 1 else q, max_sites=10)
        items = fallback_items
    
    try:
        store_docs(items)
    except Exception as e:
        pass
    
    ranked = []
    for it in items:
        source_quality = 1.0
        url = it.get("url", "")
        if "edu" in url or "gov" in url or "wikipedia" in url or "research" in url:
            source_quality = 1.3
        elif ".org" in url or "scholar" in url or "science" in url or "academic" in url:
            source_quality = 1.2
        elif "blog" in url or "forum" in url:
            source_quality = 0.9
        
        recency_bonus = 1.0
        if "fetched" in it and isinstance(it["fetched"], (int, float)):
            age_days = (time.time() - it["fetched"]) / (86400)
            if age_days < 30:
                recency_bonus = 1.1 + (0.1 * (1 - age_days/30))
        
        chunk_size = 320 if deep_research else 280
        ch = chunk_text(it.get("text", ""), max_words=chunk_size)
        chunk_count = min(6 if deep_research else 5, len(ch))
        
        top = rank_hybrid(ch, q, topk=chunk_count)
        
        boosted_top = [(c, s * source_quality * recency_bonus) for c, s in top]
        
        ranked.append({
            "url": url,
            "title": it.get("title", ""),
            "top": [{"score": float(s), "chunk": c} for c, s in boosted_top]
        })
    
    for it in ranked:
        for t in it["top"]:
            if not t["chunk"] or len(t["chunk"]) < 70:
                continue
            
            try:
                tags = f"auto:web,url:{it['url']}"
                
                if "wysokiej jakości" in it.get("title", "").lower() or t["score"] > 0.8:
                    tags += ",premium,high_quality"
                
                if ".edu" in it["url"] or ".gov" in it["url"]:
                    tags += ",trusted_source"
                
                if re.search(r"(definicja|pojęcie|termin|znaczenie)", t["chunk"].lower()):
                    tags += ",definition"
                elif re.search(r"(przykład|case study|use case|przypadek|przykładowo)", t["chunk"].lower()):
                    tags += ",example"
                elif re.search(r"(statystyka|badanie|procent|wskaźnik|dane)", t["chunk"].lower()):
                    tags += ",statistics"
                elif re.search(r"(historia|powstanie|rozwój|ewolucja)", t["chunk"].lower()):
                    tags += ",history"
                
                ltm_add(t["chunk"], tags=tags, conf=max(0.65, min(0.97, t["score"])))
            except Exception as e:
                pass
    
    ctx = []; cites = []; fact_highlights = []
    
    try:
        related_facts = ltm_search_hybrid(q, 8)
        
        tags_search_terms = q.split()[:3]
        for term in tags_search_terms:
            if len(term) > 3:
                try:
                    tag_facts = ltm_search_hybrid(term, limit=3)
                    if tag_facts:
                        related_facts.extend(tag_facts)
                except:
                    pass
        
        seen_facts = set()
        filtered_facts = []
        
        for fact in related_facts:
            if not fact.get("text") or fact.get("score", 0) <= 0.55:
                continue
            
            text = fact["text"]
            fact_hash = hashlib.md5(text.encode()).hexdigest()[:10]
            
            if (fact_hash not in seen_facts and 
                (fact.get("score", 0) > 0.6 or "fact" in fact.get("tags", "") or 
                 "premium" in fact.get("tags", "") or "high_quality" in fact.get("tags", ""))):
                seen_facts.add(fact_hash)
                filtered_facts.append(fact)
        
        for fact in filtered_facts:
            fact_highlights.append(fact["text"])
    except Exception as e:
        pass
    
    ranked.sort(key=lambda x: max([t.get("score", 0) for t in x["top"]] or [0]), reverse=True)
    
    for d in ranked:
        sorted_chunks = sorted(d["top"], key=lambda x: x.get("score", 0), reverse=True)
        for t in sorted_chunks:
            ctx.append(t["chunk"])
        cites.append({"title": d["title"], "url": d["url"]})
    
    out = {
        "query": q,
        "context": "\n\n".join(ctx[:topk]),
        "facts": fact_highlights[:max(3, topk//3)],
        "sources": cites[:max(12, topk)],
        "is_deep_research": deep_research,
        "source_count": len(items),
        "powered_by": "monolit-engine"
    }
    
    # NEW: Store fallback research results in hierarchical memory too
    if HIERARCHICAL_MEMORY_AVAILABLE and user_id:
        try:
            research_context = {
                "research_query": q,
                "deep_research": deep_research,
                "source_count": out["source_count"],
                "timestamp": time.time(),
                "research_type": "fallback_research",
                "engine": "monolit-engine"
            }
            
            research_summary = f"Fallback Research: {q} - przetworzono {out['source_count']} źródeł"
            memory_result = enhance_memory_with_hierarchy(research_summary, research_context, user_id)
            print(f"🧠 Zapisano fallback research w pamięci hierarchicznej: {memory_result.get('episode_id', 'unknown')}")
            
            out["hierarchical_memory"] = {
                "stored": True,
                "episode_id": memory_result.get("episode_id"),
                "semantic_updates": len(memory_result.get("semantic_updates", [])),
                "procedural_updates": len(memory_result.get("procedural_updates", []))
            }
            
        except Exception as e:
            print(f"[WARN] Failed to store fallback research in hierarchical memory: {e}")
            out["hierarchical_memory"] = {"stored": False, "error": str(e)}
    
    cache_put(key, out)
    return out

def answer_with_sources(q: str, deep_research: bool = False)->dict:
    from .memory import psy_tune
    data=asyncio.run(autonauka(q, topk=10, deep_research=deep_research))
    ctx=data.get("context","")
    cites=data.get("sources",[])
    facts=data.get("facts",[])
    
    facts_text = "\n\n".join([f"FAKT: {fact}" for fact in facts]) if facts else ""
    combined_ctx = f"{facts_text}\n\n{ctx}" if facts_text else ctx
    
    cite_text="\n".join([f"[{i+1}] {s['title'] or s['url']} — {s['url']}" for i,s in enumerate(cites)])
    
    t=psy_tune()
    sys_prompt = f"""Odpowiadasz po polsku. Ton: {t['tone']}. 
    Cytuj źródła w treści używając numerów w nawiasach kwadratowych [1], [2] itd.
    Bazuj tylko na podanym kontekście. Jeśli w kontekście nie ma wystarczających informacji, przyznaj to.
    Odpowiedz zwięźle, ale wyczerpująco i merytorycznie na zadane pytanie."""
    
    user_prompt = f"""Pytanie: {q}

Kontekst:
{combined_ctx}

Źródła:
{cite_text}

Odpowiedz używając dostępnych źródeł, cytując je w treści odpowiedzi. Podsumuj najważniejsze informacje i wskaź źródła."""
    
    ans=call_llm([
        {"role":"system","content":sys_prompt},
        {"role":"user","content":user_prompt}
    ], max(0.5, t.get("temperature", 0.7) - 0.1))
    
    return {
        "ok":True,
        "answer":ans,
        "sources":cites,
        "facts_used":len(facts),
        "powered_by": data.get("powered_by", "monolit-engine"),
        "is_deep_research": data.get("is_deep_research", deep_research)
    }

# ═══════════════════════════════════════════════════════════════════
# TRAVEL HELPERS
# ═══════════════════════════════════════════════════════════════════

def otm_geoname(city: str)->Optional[Tuple[float,float]]:
    if not OPENTRIPMAP_KEY: return None
    url=f"https://api.opentripmap.com/0.1/en/places/geoname?name={quote_plus(city)}&apikey={OPENTRIPMAP_KEY}"
    j=http_get_json(url); lon,lat=j.get("lon"),j.get("lat")
    try: return (float(lon), float(lat))
    except: return None

async def serp_maps(q: str, limit:int=20)->List[dict]:
    res=await serpapi_search(q, "google_maps", params={"type":"search","num":limit})
    out=[]
    data=res.get("data",{})
    for it in (data.get("local_results") or [])[:limit]:
        out.append({"title": it.get("title",""), "address": it.get("address",""), "rating": it.get("rating"), "link": it.get("links",{}).get("google_maps")})
    return out

def travel_search(city: str, what: str="attractions"):
    from urllib.request import Request, urlopen
    center=otm_geoname(city)
    if not center: return {"ok":False,"error":"geoname not found"}
    lon,lat=center
    if what=="hotels":
        items=asyncio.run(serp_maps(f"{city} hotels", 20))
    elif what=="restaurants":
        q=f"""
[out:json][timeout:25];
(
  node["amenity"~"restaurant|cafe|fast_food"](around:2200,{lat},{lon});
  way["amenity"~"restaurant|cafe|fast_food"](around:2200,{lat},{lon});
  relation["amenity"~"restaurant|cafe|fast_food"](around:2200,{lat},{lon});
);
out center 60;
"""
        req=Request(OVERPASS_URL, data=urlencode({"data": q}).encode(), headers={"Content-Type":"application/x-www-form-urlencoded"}, method="POST")
        try:
            with urlopen(req, timeout=HTTP_TIMEOUT) as r:
                j=json.loads(r.read().decode("utf-8","replace"))
            items=[]
            for e in j.get("elements",[]):
                tags=e.get("tags",{})
                items.append({"name": tags.get("name",""), "cuisine": tags.get("cuisine",""), "lat": e.get("lat") or (e.get("center") or {}).get("lat"), "lon": e.get("lon") or (e.get("center") or {}).get("lon")})
        except Exception:
            items=[]
    else:
        items=asyncio.run(serp_maps(f"{city} attractions", 20))
    return {"ok":True,"center":{"lon":lon,"lat":lat},"items":items}

# ═══════════════════════════════════════════════════════════════════
# NEWS
# ═══════════════════════════════════════════════════════════════════

async def duck_news(q: str, limit:int=10) -> Dict[str,Any]:
    from .config import WEB_USER_AGENT
    url=f"https://duckduckgo.com/html/?q={quote_plus(q)}&iar=news&ia=news"
    items=[]
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, headers={"User-Agent":WEB_USER_AGENT}) as c:
            r=await c.get(url)
            html=r.text
            for m in re.finditer(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.I|re.S):
                link=m.group(1); title=re.sub("<.*?>","",m.group(2)).strip()
                if link and title:
                    items.append({"title":title, "link":link})
                if len(items)>=limit: break
    except Exception as e:
        return {"ok":False,"error":str(e)}
    return {"ok":True,"items":items}

async def news_search(q: str, limit:int=12):
    res=await serpapi_search(q, engine="google_news", params={"num":limit})
    items=[]
    for it in (res.get("data",{}) or {}).get("news_results", [])[:limit]:
        items.append({"title": it.get("title",""), "link": it.get("link",""), "date": it.get("date","")})
    return {"ok":True,"items":items}

# ═══════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════

__all__ = [
    'autonauka', 'web_learn', 'answer_with_sources',
    'research_collect', 'serpapi_search', 'firecrawl_scrape',
    'chunk_text', 'rank_hybrid', 'store_docs',
    'travel_search', 'otm_geoname', 'serp_maps',
    'duck_news', 'news_search', 'extract_text'
]
