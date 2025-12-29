#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
advanced_cognitive_engine.py — stabilny silnik "Chat (Advanced)" (core).

Założenia:
- Zero SyntaxError, zero import-kill (brak importów projektowych na top-level).
- Stabilny kontrakt importów dla routerów:
  - CognitiveMode
  - parse_cognitive_mode
  - CognitiveRequest
  - CognitiveResult
  - AdvancedCognitiveEngine
  - AdvancedCognitiveResult
  - get_engine
  - get_advanced_cognitive_engine
  - process_with_full_cognition
- "Wydobywanie" ficzerów z projektu: lazy-load integracji (memory/semantic/inner_language/llm)
  bez wysadzania importem przy starcie serwera.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Iterable, List, Optional, Sequence, Tuple, Union
import asyncio
import os
import traceback


# =========================
# Pydantic (v1/v2) safe import
# =========================
try:
    from pydantic import BaseModel, Field  # type: ignore
except Exception as e:  # pragma: no cover
    raise RuntimeError(f"Pydantic is required but could not be imported: {e}") from e


def _pydantic_dump(model: Any) -> Dict[str, Any]:
    """
    Pydantic v2 -> model_dump
    Pydantic v1 -> dict
    """
    if hasattr(model, "model_dump"):
        return model.model_dump()  # type: ignore[attr-defined]
    return model.dict()  # type: ignore[no-any-return]


# =========================
# Public types (must be available immediately)
# =========================
class CognitiveMode(str, Enum):
    """
    Tryb pracy silnika/endpointu.
    Ujednolicone enumy z Twoich dwóch wersji, żeby router/import nie pękał.
    """
    AUTO = "auto"
    STANDARD = "standard"
    ADVANCED = "advanced"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    FAST = "fast"
    BALANCED = "balanced"
    DEEP = "deep"


DEFAULT_COGNITIVE_MODE = CognitiveMode.AUTO


def parse_cognitive_mode(value: object, default: CognitiveMode = DEFAULT_COGNITIVE_MODE) -> CognitiveMode:
    """
    Bezpieczna normalizacja trybu z requestów/env/JSON.
    Akceptuje: None/bool/int/float/str/Enum.
    """
    if value is None:
        return default
    if isinstance(value, CognitiveMode):
        return value
    if isinstance(value, bool):
        return CognitiveMode.ADVANCED if value else CognitiveMode.STANDARD
    if isinstance(value, (int, float)):
        return CognitiveMode.ADVANCED if value else CognitiveMode.STANDARD

    v = str(value).strip().lower()
    if not v:
        return default

    # po wartości
    for m in CognitiveMode:
        if v == m.value:
            return m
    # po nazwie
    for m in CognitiveMode:
        if v == m.name.lower():
            return m

    aliases: Dict[str, CognitiveMode] = {
        "default": CognitiveMode.STANDARD,
        "normal": CognitiveMode.STANDARD,
        "std": CognitiveMode.STANDARD,
        "pro": CognitiveMode.ADVANCED,
        "adv": CognitiveMode.ADVANCED,
        "analysis": CognitiveMode.ANALYTICAL,
        "analytic": CognitiveMode.ANALYTICAL,
        "creative": CognitiveMode.CREATIVE,
        "fast": CognitiveMode.FAST,
        "quick": CognitiveMode.FAST,
        "balanced": CognitiveMode.BALANCED,
        "deep": CognitiveMode.DEEP,
        "slow": CognitiveMode.DEEP,
        "auto": CognitiveMode.AUTO,
    }
    return aliases.get(v, default)


class CognitiveRequest(BaseModel):
    """
    Stabilny kontrakt wejścia dla routerów "Chat (Advanced)".
    """
    prompt: str = Field(default="")
    mode: Optional[Union[str, CognitiveMode, bool, int, float]] = Field(default=None)
    user_id: Optional[str] = Field(default=None)
    context: Dict[str, Any] = Field(default_factory=dict)
    messages: List[Dict[str, Any]] = Field(default_factory=list)

    def parsed_mode(self) -> CognitiveMode:
        return parse_cognitive_mode(self.mode)


class CognitiveResult(BaseModel):
    """
    Stabilny kontrakt wyjścia dla routerów "Chat (Advanced)".
    """
    ok: bool = Field(default=True)
    mode: str = Field(default=CognitiveMode.AUTO.value)
    output: str = Field(default="")
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = Field(default=None)

    def as_dict(self) -> Dict[str, Any]:
        return _pydantic_dump(self)


@dataclass
class AdvancedCognitiveResult:
    response: str
    metadata: Dict[str, Any]
    analysis: Dict[str, Any]
    memory: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "response": self.response,
            "metadata": self.metadata,
            "analysis": self.analysis,
            "memory": self.memory,
        }


# =========================
# Helpers
# =========================
def _safe_str(x: Any) -> str:
    try:
        return str(x)
    except Exception:
        return "<unprintable>"


def _utc_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


async def _maybe_await(x: Any) -> Any:
    if hasattr(x, "__await__"):
        return await x  # type: ignore[misc]
    return x


def _env_int(name: str, default: int) -> int:
    v = os.getenv(name, "").strip()
    if not v:
        return default
    try:
        return int(v)
    except Exception:
        return default


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name, "").strip().lower()
    if not v:
        return default
    return v in ("1", "true", "yes", "y", "on")


# =========================
# Engine
# =========================
LLMCall = Callable[[List[Dict[str, str]]], Union[str, Awaitable[str]]]


class AdvancedCognitiveEngine:
    """
    Silnik-orchestrator:
    - pobiera pamięć (jeśli masz moduł),
    - robi analizę semantyczną (jeśli masz moduł),
    - odpala inner-language (jeśli masz moduł),
    - składa prompt i woła LLM (jeśli masz wrapper),
    - zawsze zwraca stabilny wynik.
    """

    def __init__(
        self,
        llm_call: Optional[LLMCall] = None,
        logger: Optional[Callable[[str], None]] = None,
    ) -> None:
        self._llm_call = llm_call
        self._log = logger or (lambda _: None)

        # cache lazy-loaded integracji
        self._integration_loaded = False
        self._mem_search: Optional[Callable[..., Any]] = None
        self._semantic_analyze: Optional[Callable[..., Any]] = None
        self._inner_language: Optional[Any] = None

        # konfiguracja (bez “skróć historię” jako przymus)
        self._max_context_chars = _env_int("ADV_COG_MAX_CONTEXT_CHARS", 0)  # 0 = unlimited
        self._memory_limit = _env_int("ADV_COG_MEMORY_LIMIT", 12)
        self._memory_preview_chars = _env_int("ADV_COG_MEMORY_PREVIEW_CHARS", 600)
        self._messages_preview = _env_int("ADV_COG_MESSAGES_PREVIEW", 10)
        self._enable_semantic = _env_bool("ADV_COG_ENABLE_SEMANTIC", True)
        self._enable_inner_lang = _env_bool("ADV_COG_ENABLE_INNER_LANG", True)

    # ---------- lazy integrations ----------
    def _load_integrations_once(self) -> None:
        if self._integration_loaded:
            return
        self._integration_loaded = True

        # 1) memory search – próbujemy kilka wariantów modułów jakie często masz w projektach
        mem_candidates: List[Tuple[str, str]] = [
            ("core.memory", "ltm_search_hybrid"),
            ("core.memory_endpoint", "ltm_search_hybrid"),
            ("core.memory_unified", "ltm_search_hybrid"),
            ("core.unified_memory_system", "search_hybrid"),
            ("core.hierarchical_memory", "search_hybrid"),
            ("core.hier_mem", "search_hybrid"),
        ]
        for mod, fn in mem_candidates:
            try:
                m = __import__(mod, fromlist=[fn])
                f = getattr(m, fn, None)
                if callable(f):
                    self._mem_search = f
                    self._log(f"[ADV_COG] memory integration: {mod}.{fn}")
                    break
            except Exception:
                continue

        # 2) semantic analyze – jeśli masz moduł semantic
        if self._enable_semantic:
            sem_candidates: List[Tuple[str, str]] = [
                ("core.semantic", "analyze"),
                ("core.semantic_module", "analyze"),
                ("core.semantic_engine", "analyze"),
            ]
            for mod, fn in sem_candidates:
                try:
                    m = __import__(mod, fromlist=[fn])
                    f = getattr(m, fn, None)
                    if callable(f):
                        self._semantic_analyze = f
                        self._log(f"[ADV_COG] semantic integration: {mod}.{fn}")
                        break
                except Exception:
                    continue

        # 3) inner language – jeśli masz obiekt/klasę
        if self._enable_inner_lang:
            inner_candidates: List[str] = [
                "core.inner_language",
                "core.inner_language_engine",
                "core.inner_language_module",
            ]
            for mod in inner_candidates:
                try:
                    m = __import__(mod, fromlist=["*"])
                    # szukamy typowych nazw obiektu
                    obj = getattr(m, "inner_language", None) or getattr(m, "ENGINE", None) or getattr(m, "engine", None)
                    if obj is not None:
                        self._inner_language = obj
                        self._log(f"[ADV_COG] inner_language integration: {mod} (object)")
                        break
                    # albo klasy
                    cls = getattr(m, "InnerLanguage", None) or getattr(m, "InnerLanguageEngine", None)
                    if cls is not None:
                        self._inner_language = cls()
                        self._log(f"[ADV_COG] inner_language integration: {mod} (class instance)")
                        break
                except Exception:
                    continue

        # 4) LLM wrapper – jeśli nie podano llm_call, spróbuj wyciągnąć z projektu
        if self._llm_call is None:
            llm_candidates: List[Tuple[str, str]] = [
                ("core.llm", "call_llm"),
                ("core.llm", "call_llm_chat"),
                ("core.llm_client", "call_llm"),
                ("core.openai_compat", "call_llm"),
            ]
            for mod, fn in llm_candidates:
                try:
                    m = __import__(mod, fromlist=[fn])
                    f = getattr(m, fn, None)
                    if callable(f):
                        # owijka do formatu List[dict]
                        def _wrapped(messages: List[Dict[str, str]], _f: Any = f) -> Any:
                            return _f(messages)

                        self._llm_call = _wrapped
                        self._log(f"[ADV_COG] llm integration: {mod}.{fn}")
                        break
                except Exception:
                    continue

    # ---------- core processing ----------
    async def process(
        self,
        user_message: str,
        conversation_context: Optional[List[Dict[str, Any]]] = None,
        user_id: Optional[str] = None,
        mode: Optional[object] = None,
    ) -> AdvancedCognitiveResult:
        self._load_integrations_once()

        t0 = datetime.utcnow()
        msg = (user_message or "").strip()

        parsed_mode = parse_cognitive_mode(mode)
        analysis: Dict[str, Any] = {
            "mode": parsed_mode.value,
            "intent": "question" if "?" in msg else "statement",
            "len": len(msg),
            "ts": _utc_iso(),
        }

        # semantic analyze (optional)
        if self._semantic_analyze is not None:
            try:
                sem = self._semantic_analyze(msg)
                sem = await _maybe_await(sem)
                if isinstance(sem, dict):
                    analysis["semantic"] = sem
            except Exception as e:
                analysis["semantic_error"] = _safe_str(e)

        # inner language (optional)
        if self._inner_language is not None:
            try:
                ctx_data = {
                    "conversation_length": len(conversation_context or []),
                    "recent_messages": (conversation_context or [])[-3:],
                    "mode": parsed_mode.value,
                }
                proc = None
                if hasattr(self._inner_language, "process_natural_language_input"):
                    proc = getattr(self._inner_language, "process_natural_language_input")
                elif hasattr(self._inner_language, "process"):
                    proc = getattr(self._inner_language, "process")
                if callable(proc):
                    out = proc(msg, ctx_data)
                    out = await _maybe_await(out)
                    if isinstance(out, dict):
                        analysis["inner_language"] = out
            except Exception as e:
                analysis["inner_language_error"] = _safe_str(e)

        # memory retrieval (optional)
        memory_items: List[Dict[str, Any]] = []
        if self._mem_search is not None and msg:
            try:
                out = None
                # różne sygnatury – próbujemy bezpiecznie
                try:
                    out = self._mem_search(query=msg, user_id=user_id, max_results=self._memory_limit)
                except TypeError:
                    try:
                        out = self._mem_search(q=msg, user_id=user_id, max_results=self._memory_limit)
                    except TypeError:
                        try:
                            out = self._mem_search(msg, limit=self._memory_limit)
                        except TypeError:
                            out = self._mem_search(msg)
                out = await _maybe_await(out)
                if isinstance(out, list):
                    for it in out[: self._memory_limit]:
                        if isinstance(it, dict):
                            memory_items.append(it)
                        else:
                            memory_items.append({"text": _safe_str(it)})
            except Exception as e:
                analysis["memory_error"] = _safe_str(e)

        # build prompt (no forced shortening)
        prompt = self._build_prompt(
            user_message=msg,
            conversation_context=conversation_context or [],
            memory_items=memory_items,
            mode=parsed_mode,
        )

        # call llm (optional)
        response_text = ""
        meta: Dict[str, Any] = {
            "engine": "advanced",
            "mode": parsed_mode.value,
            "ts": _utc_iso(),
        }

        if self._llm_call is not None:
            try:
                messages = self._build_messages(prompt=prompt, mode=parsed_mode)
                out = self._llm_call(messages)
                out = await _maybe_await(out)
                response_text = (out or "").strip()
            except Exception as e:
                meta["llm_error"] = _safe_str(e)
                meta["llm_trace"] = traceback.format_exc(limit=6)

        if not response_text:
            # fallback – nigdy nie zwracamy pustki
            response_text = msg if msg else "OK"

        meta["dur_ms"] = int((datetime.utcnow() - t0).total_seconds() * 1000)
        meta["memory_items"] = len(memory_items)
        meta["ctx_messages"] = len(conversation_context or [])

        return AdvancedCognitiveResult(
            response=response_text,
            metadata=meta,
            analysis=analysis,
            memory=memory_items,
        )

    def _build_messages(self, prompt: str, mode: CognitiveMode) -> List[Dict[str, str]]:
        system_lines = [
            "Jesteś zaawansowanym asystentem.",
            "Odpowiadasz konkretnie, po polsku, bez lania wody.",
            "Jeśli użytkownik poda kod/logi, analizujesz je technicznie i proponujesz konkretne poprawki.",
        ]
        if mode in (CognitiveMode.ANALYTICAL, CognitiveMode.DEEP):
            system_lines.append("Tryb: analiza. Priorytet: poprawność, pełne wnioski, brak skrótów.")
        elif mode in (CognitiveMode.CREATIVE,):
            system_lines.append("Tryb: kreatywny, ale nadal precyzyjny i techniczny, bez konfabulacji.")
        elif mode in (CognitiveMode.FAST,):
            system_lines.append("Tryb: szybki. Krócej, ale nadal rzeczowo.")
        else:
            system_lines.append("Tryb: zbalansowany.")

        return [
            {"role": "system", "content": "\n".join(system_lines)},
            {"role": "user", "content": prompt},
        ]

    def _build_prompt(
        self,
        user_message: str,
        conversation_context: List[Dict[str, Any]],
        memory_items: List[Dict[str, Any]],
        mode: CognitiveMode,
    ) -> str:
        lines: List[str] = []
        lines.append(f"[MODE] {mode.value}")

        if memory_items:
            lines.append("\n[PAMIĘĆ]")
            for it in memory_items[: self._memory_limit]:
                txt = it.get("text") or it.get("content") or it.get("summary") or it.get("value") or ""
                txt = str(txt).strip()
                if txt:
                    lines.append(f"- {txt[: self._memory_preview_chars]}")

        if conversation_context:
            # nie “skracamy historii” jako degradacja; robimy tylko ochronę przed absurdem,
            # i to WYŁĄCZONE domyślnie (max_context_chars=0).
            ctx = conversation_context
            if self._messages_preview > 0 and len(ctx) > self._messages_preview:
                ctx = ctx[-self._messages_preview :]

            lines.append("\n[KONTEKST ROZMOWY]")
            for m in ctx:
                role = str(m.get("role", "user"))
                content = str(m.get("content", "")).strip()
                if not content:
                    continue
                lines.append(f"{role}: {content}")

        lines.append("\n[UŻYTKOWNIK]")
        lines.append(user_message)

        full = "\n".join(lines).strip()
        if self._max_context_chars and len(full) > self._max_context_chars:
            # twardy limit tylko jeśli ktoś go USTAWI envem
            full = full[-self._max_context_chars :]

        return full


# =========================
# Compatibility wrapper for router
# =========================
async def process_with_full_cognition(
    prompt: str,
    messages: Optional[List[Dict[str, Any]]] = None,
    user_id: Optional[str] = None,
    mode: Optional[object] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Funkcja kompatybilności, bo router często woli importować "process_with_full_cognition".
    Zwraca słownik stabilny do JSON: response + metadata + analysis + memory
    """
    engine = get_engine()
    conv = messages or []
    res = await engine.process(
        user_message=prompt,
        conversation_context=conv,
        user_id=user_id,
        mode=mode,
    )
    out = res.to_dict()
    if context:
        # kontekst dodatkowy (nie nadpisujemy, dokładamy)
        out.setdefault("metadata", {}).setdefault("context", {}).update(context)
    return out


_DEFAULT_ENGINE: Optional[AdvancedCognitiveEngine] = None


def get_engine() -> AdvancedCognitiveEngine:
    global _DEFAULT_ENGINE
    if _DEFAULT_ENGINE is None:
        _DEFAULT_ENGINE = AdvancedCognitiveEngine()
    return _DEFAULT_ENGINE


def get_advanced_cognitive_engine() -> AdvancedCognitiveEngine:
    return get_engine()


__all__ = [
    "CognitiveMode",
    "parse_cognitive_mode",
    "CognitiveRequest",
    "CognitiveResult",
    "AdvancedCognitiveEngine",
    "AdvancedCognitiveResult",
    "get_engine",
    "get_advanced_cognitive_engine",
    "process_with_full_cognition",
]
