#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Writing Module - Creative writing, Vinted, social media, auctions
FULL LOGIC - NO PLACEHOLDERS!
"""
import re

import re, random, time
from typing import Dict, List, Optional

from .config import FASHION, PL_SYNONYMS, PL_COLLOC
from .helpers import log_error, make_id as _id_for, tokenize as _tok
from .memory import psy_tune, _db, ltm_add
from .llm import call_llm
import json


# ═══════════════════════════════════════════════════════════════════
# TEXT ENRICHMENT
# ═══════════════════════════════════════════════════════════════════

def _enrich(text: str) -> str:
    """Wzbogać tekst synonimami i kolokacjami"""
    out = text
    for k, vals in PL_SYNONYMS.items():
        if k in out:
            out = out.replace(k, f"{k}/{random.choice(vals)}")
    if random.random() < 0.6:
        out += "\n\n" + " • ".join(random.sample(PL_COLLOC, k=min(3, len(PL_COLLOC))))
    return out


def _anti_repeat(s: str) -> str:
    """Usuń powtórzenia linii"""
    lines = [x.strip() for x in s.splitlines() if x.strip()]
    seen = set()
    out = []
    for ln in lines:
        key = re.sub(r"\W+", " ", ln.lower()).strip()
        if key in seen:
            continue
        seen.add(key)
        out.append(ln)
    return "\n".join(out)


def _bounded_length(s: str, target: str) -> str:
    """Ogranicz długość tekstu do celu"""
    caps = {"krótki": 800, "średni": 1600, "długi": 3000, "bardzo długi": 6000}
    cap = caps.get(target, 3000)
    return s if len(s) <= cap else s[:cap]


# ═══════════════════════════════════════════════════════════════════
# FASHION ANALYSIS
# ═══════════════════════════════════════════════════════════════════

def analyze_fashion_text(txt: str) -> Dict[str, List[str]]:
    """Analiza tekstu pod kątem elementów mody"""
    SIZE_PAT = re.compile(r"\b(XXS|XS|S|M|L|XL|XXL|3XL|4XL|EU\s?\d{2}|US\s?\d{1,2})\b", re.I)
    t = (txt or "").lower()
    
    out = {
        "brands": [], "materials": [], "sizes": [], "colors": [],
        "categories": [], "fits": [], "features": [], "patterns": [],
        "occasions": [], "styles": [], "closures": []
    }
    
    COLORS = ["czarny", "biały", "czerwony", "zielony", "niebieski", "żółty", "brązowy", 
              "różowy", "fioletowy", "szary", "beżowy", "granatowy", "turkusowy", 
              "oliwkowy", "błękitny", "bordowy", "kremowy", "ecru"]
    
    cats = ["koszulka", "t-shirt", "bluza", "spodnie", "jeansy", "sukienka", "kurtka", 
            "płaszcz", "marynarka", "sweter", "buty", "sneakersy", "trampki", "torebka", 
            "plecak", "spódnica", "dresy", "legginsy", "szorty"]
    
    for b in FASHION["brands"]:
        if re.search(rf"\b{re.escape(b)}\b", t):
            out["brands"].append(b)
    
    for m in FASHION["materials"]:
        if re.search(rf"\b{re.escape(m)}\b", t):
            out["materials"].append(m)
    
    for c in COLORS:
        if re.search(rf"\b{re.escape(c)}\b", t):
            out["colors"].append(c)
    
    for cat in cats:
        if re.search(rf"\b{re.escape(cat)}\b", t):
            out["categories"].append(cat)
    
    for f in FASHION["fits"]:
        if re.search(rf"\b{re.escape(f)}\b", t):
            out["fits"].append(f)
    
    for feat in FASHION["features"]:
        if re.search(rf"\b{re.escape(feat)}\b", t):
            out["features"].append(feat)
    
    for pat in FASHION["patterns"]:
        if re.search(rf"\b{re.escape(pat)}\b", t):
            out["patterns"].append(pat)
    
    for occ in FASHION["occasions"]:
        if re.search(rf"\b{re.escape(occ)}\b", t):
            out["occasions"].append(occ)
    
    for st in FASHION["styles"]:
        if re.search(rf"\b{re.escape(st)}\b", t):
            out["styles"].append(st)
    
    for cl in FASHION["closures"]:
        if re.search(rf"\b{re.escape(cl)}\b", t):
            out["closures"].append(cl)
    
    for m in SIZE_PAT.findall(txt or ""):
        out["sizes"].append(m.upper())
    
    # Heurystyka "buty"
    for b in out["brands"]:
        idx = t.find(b)
        if idx != -1 and "buty" in t[max(0, idx - 40):idx + 40]:
            if "buty" not in out["categories"]:
                out["categories"].append("buty")
    
    # Deduplikacja
    for k in out:
        out[k] = list(dict.fromkeys(out[k]))
    
    return out


# ═══════════════════════════════════════════════════════════════════
# WRITING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def write_creative_boost(topic: str, tone: str, styl: str, dlugosc: str, web_ctx: str = "") -> str:
    """Kreatywne pisanie z LLM"""
    t = psy_tune()
    
    # Jeśli nie ma kontekstu web, spróbuj pozyskać go automatycznie
    if not web_ctx:
        try:
            from core.research import autonauka
            import asyncio
            web_result = asyncio.run(autonauka(topic, topk=4))
            if web_result and isinstance(web_result, dict) and web_result.get("context"):
                web_ctx = web_result["context"][:1500]  # Limit długości
                print(f"[WRITING] Automatycznie pozyskano kontekst z sieci dla tematu: {topic}")
        except Exception as e:
            print(f"[WRITING] Nie udało się pozyskać kontekstu z sieci: {str(e)}")
    
    # Step 1: Outline
    outline = call_llm([
        {"role": "system", "content": "Konspektysta. Twórz szkielet 6–10 punktów z progresją i mini tezami."},
        {"role": "user", "content": f"Temat: {topic}\nTon: {tone or t['tone']}\nStyl: {styl}\nUżyj wiedzy:\n{web_ctx or ''}"}
    ], max(t["temperature"] - 0.1, 0.5))
    
    # Step 2: Draft
    draft = call_llm([
        {"role": "system", "content": "Pisarz PL. Rozwiń konspekt w spójny tekst. Klarownie, bez lania wody."},
        {"role": "user", "content": f"Konspekt:\n{outline}"}
    ], t["temperature"])
    
    # Step 3: Polish
    polish = call_llm([
        {"role": "system", "content": "Redaktor PL. Usuń tautologie, wyrównaj rejestr, dodaj płynne przejścia."},
        {"role": "user", "content": draft}
    ], max(0.6, t["temperature"] - 0.05))
    
    styled = _bounded_length(_anti_repeat(_enrich(polish)), dlugosc)
    return styled


def write_vinted(title: str, desc: str, price: Optional[float] = None, web_ctx: str = "") -> str:
    """Generator opisów Vinted. Z fallbackiem, gdy LLM niedostępny."""
    attrs = analyze_fashion_text((title or "") + " " + (desc or ""))
    meta = []
    
    if attrs.get("sizes"):
        meta.append("Rozmiar: " + ", ".join(attrs["sizes"]))
    if attrs.get("materials"):
        meta.append("Materiał: " + ", ".join(attrs["materials"]))
    if attrs.get("colors"):
        meta.append("Kolor: " + ", ".join(attrs["colors"]))
    
    spec = (" • ".join(meta)) if meta else ""
    t = psy_tune()
    
    prompt = f"""Platforma: Vinted (PL).
Tytuł: {title}
Opis: {desc}
{('Parametry: ' + spec) if spec else ''}
Cena: {price if price else 'brak'}
Wymagania: krótko, konkretnie, stan, rozmiar, 5–8 hashtagów."""
    
    out = call_llm([
        {"role": "system", "content": "Sprzedawca Vinted PL. Same konkrety."},
        {"role": "user", "content": prompt}
    ], max(0.55, t["temperature"] - 0.1))
    
    if out.startswith("[LLM-OFF]") or out.startswith("[LLM-ERR]") or out.startswith("[LLM-FAIL]"):
        base = [
            f"{title}",
            "Stan: bardzo dobry",
            spec,
            (f"Cena: {price} PLN" if price else ""),
            "#vinted #sprzedam #moda #outfit"
        ]
        out = "\n".join([ln for ln in base if ln])
    
    return _anti_repeat(out)


def write_social(platform: str, topic: str, tone: str = "dynamiczny", hashtags: int = 6, variants: int = 3, web_ctx: str = "") -> str:
    """Generator krótkich postów do social mediów."""
    t = psy_tune()
    
    ctx = ("Kontekst:" + chr(10) + web_ctx.strip() + "\n") if web_ctx else ""
    prompt = (
        f"Platforma: {platform}\n"
        f"Temat: {topic}\n"
        f"Ton: {tone}\n"
        f"Hashtagi: {hashtags}\n"
        f"{ctx}"
        "Wymagania: krótki hook, 1 insight, CTA, lista hashtagów."
    )

    
    out = call_llm([
        {"role": "system", "content": "Twórca social PL. Krótko i rzeczowo."},
        {"role": "user", "content": prompt}
    ], max(0.6, t["temperature"] - 0.05))
    
    if out.startswith("[LLM-OFF]") or out.startswith("[LLM-ERR]") or out.startswith("[LLM-FAIL]"):
        out = f"{topic} — więcej szczegółów wkrótce. #update"
    
    return _anti_repeat(out)


def write_auction(title: str, desc: str, price: Optional[float] = None, tags: List[str] = [], web_ctx: str = "") -> str:
    """Pisanie ogłoszeń aukcyjnych"""
    t = psy_tune()
    attrs = _enrich(f"Tytuł: {title}\nOpis: {desc}\nCena: {price}\nTagi: {', '.join(tags)}")
    
    return call_llm([
        {"role": "system", "content": "Copywriter sprzedażowy PL. 1 główny benefit, 2 dowody, sensoryka, bariera ryzyka, CTA. Daj wariant A/B."},
        {"role": "user", "content": attrs + ("\n\n[Źródła]" + chr(10) + web_ctx if web_ctx else "")}
    ], max(0.55, t["temperature"] - 0.05))


def write_auction_pro(title: str, desc: str, price: Optional[float] = None, web_ctx: str = "", tone: str = "sprzedażowy", length: str = "średni", kreatywny: bool = False) -> str:
    """Aukcje PRO – mocniejszy generator"""
    attrs = analyze_fashion_text((title or "") + " " + (desc or ""))
    
    # Wzbogacenie z KB
    kb = auction_kb_fetch()
    enrich_lines = []
    for k, v in kb.items():
        if v:
            sample = ", ".join(list(v)[:5])
            enrich_lines.append(f"{k}: {sample}")
    enrich_txt = "\n".join(enrich_lines)
    
    meta = []
    if attrs.get("brands"):
        meta.append("Marka: " + ", ".join(attrs["brands"]))
    if attrs.get("materials"):
        meta.append("Materiał: " + ", ".join(attrs["materials"]))
    if attrs.get("fits"):
        meta.append("Fason: " + ", ".join(attrs["fits"]))
    if attrs.get("sizes"):
        meta.append("Rozmiar: " + ", ".join(attrs["sizes"]))
    if attrs.get("colors"):
        meta.append("Kolor: " + ", ".join(attrs["colors"]))
    if attrs.get("features"):
        meta.append("Cechy: " + ", ".join(attrs["features"]))
    if attrs.get("patterns"):
        meta.append("Wzór: " + ", ".join(attrs["patterns"]))
    if attrs.get("styles"):
        meta.append("Styl: " + ", ".join(attrs["styles"]))
    if attrs.get("closures"):
        meta.append("Zapięcie: " + ", ".join(attrs["closures"]))
    
    meta_str = "\n".join(meta)
    
    prompt = f"""Napisz opis aukcji PL (2 wersje A/B, bez powtórzeń, precyzyjny).
Ton: {tone}. Długość: {length}.
Produkt: {title}
Opis sprzedawcy: {desc}
Cena: {price if price is not None else 'brak'}

Atrybuty rozpoznane:
{meta_str or '(brak)'}

Zasoby marki/mody (KB):
{enrich_txt or '(brak)'}

Wymagania:
- 1 hook sensoryczny, 1 benefit główny, 2 dowody (materiał/wykonanie/opinie), parametry (rozmiar/wymiary jeśli są), wskazówki pielęgnacji (jeśli pasują).
- krótka sekcja „Dlaczego warto", „Wysyłka i zwroty" (neutralnie).
- Unikaj tautologii, nie powtarzaj zdań. Dodaj 6–10 hashtagów modowych na końcu.
{('[Źródła]' + chr(10) + web_ctx) if web_ctx else ''}"""
    
    t = psy_tune()
    out = call_llm([
        {"role": "system", "content": "Copywriter e-commerce PL, precyzyjny, zero lania wody."},
        {"role": "user", "content": prompt}
    ], max(0.58, t["temperature"] - 0.1))
    
    if out.startswith("[LLM-OFF]") or out.startswith("[LLM-ERR]") or out.startswith("[LLM-FAIL]"):
        # Fallback deterministyczny
        lines = []
        lines.append(f"{title} — opis A:")
        lines.append(f"- Stan: {('jak nowy' if 'stan' in desc.lower() or 'idealny' in desc.lower() else 'bardzo dobry')}")
        if meta_str:
            lines.append(meta_str)
        if price is not None:
            lines.append(f"- Cena: {price} PLN (do rozsądnej negocjacji)")
        care = random.choice(FASHION["care"])
        lines.append(f"- Pielęgnacja: {care}")
        lines.append("Dlaczego warto: solidne wykonanie, komfort noszenia, łatwe łączenie w stylizacjach.")
        lines.append("Wysyłka i zwroty: szybka wysyłka 24–48h, możliwość zwrotu zgodnie z regulaminem.")
        lines.append("")
        lines.append(f"{title} — opis B:")
        lines.append("Hook: Lekki jak piórko, a trzyma formę — idealny do codziennych stylizacji.")
        if meta_str:
            lines.append(meta_str)
        cat_tag = attrs['categories'][0] if attrs.get('categories') else 'moda'
        cat_tag_clean = re.sub(r"\W+", "", cat_tag)
        lines.append(f"Hashtagi: #{cat_tag_clean} #okazja #premium #styl #outfit #nowość")
        out = "\n".join(lines)
    
    out = _anti_repeat(out)
    return _bounded_length(_enrich(out), length)


# ═══════════════════════════════════════════════════════════════════
# AUCTION KB (Knowledge Base)
# ═══════════════════════════════════════════════════════════════════

def auction_kb_learn(items: List[dict]) -> int:
    """Naucz KB z aukcji"""
    if not items:
        return 0
    
    conn = _db()
    c = conn.cursor()
    n = 0
    
    for it in items:
        kind = str(it.get("kind", "")).strip()[:32] or "generic"
        key = str(it.get("key", "")).strip()[:64]
        val = str(it.get("val", "")).strip()[:400]
        w = float(it.get("weight", 0.7))
        
        if not key or not val:
            continue
        
        kid = _id_for(f"{kind}:{key}:{val}")
        c.execute("INSERT OR REPLACE INTO kb_auction VALUES(?,?,?,?,?,?)", (kid, kind, key, val, w, time.time()))
        n += 1
        
        # Dodaj też do LTM
        try:
            ltm_add(f"[KB:{kind}] {key}: {val}", "kb:auction", w)
        except:
            pass
    
    conn.commit()
    conn.close()
    return n


def auction_kb_fetch() -> Dict[str, set]:
    """Pobierz KB aukcji"""
    conn = _db()
    c = conn.cursor()
    rows = c.execute("SELECT kind,key,val,weight FROM kb_auction ORDER BY ts DESC LIMIT 800").fetchall()
    conn.close()
    
    out: Dict[str, set] = {}
    for r in rows:
        out.setdefault(f"{r['kind']}:{r['key']}", set()).add(r["val"])
    
    return out


def suggest_tags_for_auction(title: str, desc: str) -> List[str]:
    """Sugeruj tagi dla aukcji"""
    attrs = analyze_fashion_text((title or "") + " " + (desc or ""))
    tags = []
    
    for k in ("brands", "categories", "styles", "materials", "colors", "fits", "features"):
        for v in attrs.get(k, []):
            tags.append("#" + re.sub(r"\s+", "", v.lower()))
    
    # Dodaj KB
    kb = auction_kb_fetch()
    for k, vals in kb.items():
        for v in list(vals)[:3]:
            tags.append("#" + re.sub(r"\s+", "", v.lower()))
    
    tags = list(dict.fromkeys(tags))
    return tags[:12]


# ═══════════════════════════════════════════════════════════════════
# MISTRZOWSKIE PISANIE TEKSTÓW - 100 LVL
# ═══════════════════════════════════════════════════════════════════

def write_masterpiece_article(topic: str, style: str = "zaangażowany", length: str = "długi", target_audience: str = "ogólny", seo_optimized: bool = True) -> str:
    """
    MISTRZOWSKIE PISANIE ARTYKUŁÓW
    Na poziomie najlepszych copywriterów świata
    """
    # Zawsze zbadaj temat - musi mieć web access!
    research = ""
    try:
        # Preferuj autonauka zamiast web_learn
        from .research import autonauka
        import asyncio
        result = asyncio.run(autonauka(topic, topk=8, deep_research=True))
        if result and isinstance(result, dict):
            research = result.get("context", "")
            if result.get("facts"):
                research = "KLUCZOWE FAKTY:\n" + "\n".join(result["facts"]) + "\n\n" + research
            research = f"\n\nBadania na temat:\n{research[:3000]}" if research else ""
        print(f"[WRITING] Automatycznie pozyskano rozszerzone dane do artykułu: {topic}")
    except Exception as e:
        print(f"[WRITING] Błąd podczas pozyskiwania danych z sieci: {str(e)}")
        # Fallback do web_learn jeśli autonauka zawiedzie
        try:
            from .research import web_learn
            learn_result = web_learn(topic, mode="fast")
            if learn_result and isinstance(learn_result, dict) and learn_result.get("draft"):
                research = f"\n\nBadania na temat:\n{learn_result['draft'][:2000]}" 
        except:
            pass

    # Psychika wpływa na styl
    psyche = psy_tune()

    prompt = f"""
JESTEŚ MISTRZEM KREATYWNYCH TEKSTÓW - piszesz artykuły na poziomie światowych bestsellerów.

🎯 TEMAT: {topic}
🎨 STYL: {style}
📏 DŁUGOŚĆ: {length}
👥 GRUPA DOCELOWA: {target_audience}

🔥 TWÓJ STYL PISANIA:
- Zaczynaj od mocnego hooka, który wbija w fotel
- Buduj napięcie i ciekawość przez cały tekst
- Używaj storytellingu - historie są lepsze niż suche fakty
- Pisz językiem żywym, obrazowym, emocjonalnym
- Kończ call-to-action który motywuje do działania
- Jeśli SEO - naturalnie wpleć słowa kluczowe

📚 STRUKTURA ARTYKUŁU:
1. HOOK (pierwsze 3-5 zdań - musi zaciekawić)
2. PROBLEM (nazwij ból czytelnika)
3. ROZWIĄZANIE (zaprezentuj swoją wiedzę/rozwiązanie)
4. DOWODY (przykłady, historie, statystyki)
5. KONKLUZJA (podsumuj i zmotywuj)
6. CTA (wezwanie do działania)

{research}

Pisz jak mistrz copywritingu - tekst ma być tak dobry, że czytelnik nie może przestać czytać!
"""

    try:
        result = call_llm([
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Napisz artykuł na temat: {topic}"}
        ], temperature=max(0.7, psyche.get("temperature", 0.7)), max_tokens=4000)

        # Wzbogać tekst jeśli potrzeba
        if len(result) < 2000 and length == "bardzo długi":
            result += "\n\n" + call_llm([
                {"role": "system", "content": "Rozszerz ten artykuł o dodatkowe sekcje i przykłady."},
                {"role": "user", "content": result[:500]}
            ], max_tokens=2000)

        return result

    except Exception as e:
        log_error(f"Masterpiece article error: {e}")
        return f"Przepraszam, nie udało się wygenerować artykułu na temat {topic}. Spróbuj ponownie."

def write_sales_masterpiece(product_name: str, product_desc: str, target_price: float = None, audience: str = "ogólny", urgency: str = "normalna") -> str:
    """
    MISTRZ SPRZEDAŻY - teksty które sprzedają lepiej niż konkurencja
    """
    psyche = psy_tune()

    urgency_multipliers = {
        "niska": 0.6,
        "normalna": 0.8,
        "wysoka": 1.0,
        "krytyczna": 1.2
    }

    temp = max(0.6, psyche.get("temperature", 0.7) * urgency_multipliers.get(urgency, 0.8))

    prompt = f"""
JESTEŚ MISTRZEM SPRZEDAŻY - twoje teksty sprzedają lepiej niż konkurencja.

🎯 PRODUKT: {product_name}
📝 OPIS: {product_desc}
💰 CENA: {target_price or "nie podana"}
👥 GRUPA DOCELOWA: {audience}
⏰ PILNOŚĆ: {urgency}

🔥 STRATEGIA SPRZEDAŻOWA:
1. PROBLEM - nazwij ból który produkt rozwiązuje
2. ROZWIĄZANIE - pokaż jak produkt rozwiązuje ten ból
3. BENEFITY - konkretne korzyści dla klienta
4. DOWODY SPOŁECZNE - opinie, statystyki, przykłady
5. RYZYKO - usuń wszystkie wątpliwości
6. URZĄDZENIE - ograniczona oferta jeśli urgency wysoka
7. CTA - mocne wezwanie do zakupu

💪 PSYCHOLOGIA SPRZEDAŻY:
- Używaj emocji - strach przed stratą, radość z korzyści
- Buduj zaufanie - konkretne fakty i liczby
- Twórz pilność - jeśli potrzeba
- Pisz językiem korzyści, nie cech

Pisz tekst który sprzedaje - czytelnik ma poczuć że MUSI to kupić!
"""

    try:
        result = call_llm([
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Napisz opis sprzedażowy produktu: {product_name}"}
        ], temperature=temp, max_tokens=2000)

        return result

    except Exception as e:
        log_error(f"Sales masterpiece error: {e}")
        return f"Nie udało się wygenerować opisu sprzedażowego dla {product_name}."

def write_technical_masterpiece(topic: str, difficulty: str = "średni", include_examples: bool = True, include_code: bool = True) -> str:
    """
    MISTRZ TECHNICZNYCH WYJAŚNIEŃ
    Tłumaczysz trudne rzeczy jak dla 5-latka, ale kompletnie
    """
    psyche = psy_tune()

    prompt = f"""
JESTEŚ MISTRZEM TECHNICZNYCH WYJAŚNIEŃ - tłumaczysz trudne rzeczy prosto.

🎯 TEMAT: {topic}
📊 POZIOM TRUDNOŚCI: {difficulty}
💻 PRZYKŁADY: {'tak' if include_examples else 'nie'}
🔧 KOD: {'tak' if include_code else 'nie'}

🔥 TWÓJ STYL TŁUMACZENIA:
- Zaczynaj od analogii z życia codziennego
- Buduj krok po kroku - od prostego do złożonego
- Używaj konkretnych przykładów i metafor
- Jeśli kod - pisz kompletny, działający kod z komentarzami
- Kończ podsumowaniem i kolejnymi krokami

📚 STRUKTURA WYJAŚNIENIA:
1. ANALOGIA (coś znajomego)
2. PODSTAWY (najprostsze elementy)
3. BUDOWA (jak to działa)
4. PRZYKŁADY (konkretne przypadki)
5. KOD (jeśli potrzeba)
6. PODSUMOWANIE (co dalej)

Pisz jak nauczyciel który kocha swój przedmiot i chce żeby uczeń zrozumiał!
"""

    try:
        result = call_llm([
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Wyjaśnij: {topic}"}
        ], temperature=max(0.5, psyche.get("temperature", 0.7)), max_tokens=3000)

        return result

    except Exception as e:
        log_error(f"Technical masterpiece error: {e}")
        return f"Nie udało się wyjaśnić tematu {topic}. Spróbuj ponownie."

# ═══════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════

__all__ = [
    '_enrich', '_anti_repeat', '_bounded_length',
    'analyze_fashion_text',
    'write_creative_boost', 'write_vinted', 'write_social',
    'write_auction', 'write_auction_pro',
    'auction_kb_learn', 'auction_kb_fetch', 'suggest_tags_for_auction',
    'write_masterpiece_article', 'write_sales_masterpiece', 'write_technical_masterpiece'
]
