"""
Knowledge Compressor – wersja ulepszona
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import defaultdict
import hashlib
import random
import math

import numpy as np  # zakładam, że jest w środowisku

from .config import *
from .llm import get_llm_client
from .memory import get_memory_manager
from .hierarchical_memory import get_hierarchical_memory
from .helpers import log_info, log_error, log_warning


# --------------------------- Stałe i pomocnicze ---------------------------

MAX_PROMPT_CHARS = 8000       # twardy limit wejścia do LLM
MIN_FLOAT = -1.0
MAX_FLOAT = 1.0


def _clamp(x: float, lo=MIN_FLOAT, hi=MAX_FLOAT) -> float:
    return max(lo, min(hi, x))


async def _chat_text(llm_client, messages) -> str:
    """
    Ujednolicone wywołanie LLM.
    Zwraca plain text niezależnie od tego, czy backend zwraca string czy payload w stylu OpenAI.
    """
    resp = await llm_client.chat_completion(messages)
    if isinstance(resp, str):
        return resp
    try:
        return resp["choices"][0]["message"]["content"]
    except Exception:
        return json.dumps(resp, ensure_ascii=False)


def _now() -> datetime:
    return datetime.now()


# --------------------------- Modele danych ---------------------------

@dataclass
class KnowledgeVector:
    vector_id: str
    dimensions: int
    embedding: List[float]
    compression_ratio: float
    source_conversations: List[str]
    dominant_themes: List[str]
    emotional_signature: Dict[str, float]
    temporal_weight: float
    confidence_score: float
    created_at: datetime
    last_updated: datetime
    usage_count: int


@dataclass
class ThinkingPattern:
    pattern_id: str
    pattern_type: str
    trigger_contexts: List[str]
    typical_responses: List[str]
    success_rate: float
    frequency: int
    last_seen: datetime
    evolution_trajectory: List[Dict[str, Any]]


@dataclass
class SyntheticMemory:
    memory_id: str
    compressed_content: str
    abstraction_level: int  # 1-5
    generalization_power: float
    applicable_contexts: List[str]
    derived_from: List[str]
    predictive_value: float


# --------------------------- Kompresor ---------------------------

class KnowledgeCompressor:
    """
    Silnik kompresji wiedzy – wersja asynchroniczna i odporna na błędy.
    """

    # stałe konfiguracyjne
    VECTOR_DIM = 128
    THEMES_MAX = 8
    SAMPLE_CONV = 5
    MAX_FRAGMENT = 200

    def __init__(self):
        self.llm_client = get_llm_client()
        self.memory = get_memory_manager()
        self.hierarchical_memory = get_hierarchical_memory()

        self.knowledge_vectors: Dict[str, KnowledgeVector] = {}
        self.thinking_patterns: Dict[str, ThinkingPattern] = {}
        self.synthetic_memories: Dict[str, SyntheticMemory] = {}

        self.compression_stats = {
            "total_compressed": 0,
            "compression_ratio_avg": 0.0,
            "patterns_discovered": 0,
            "synthetic_memories_created": 0
        }

        self._lock = asyncio.Lock()
        log_info("[KNOWLEDGE_COMPRESSOR] Init OK")

    # -------------------- Public API --------------------

    async def compress_conversations(self, conversations: List[Dict[str, Any]], user_id: str) -> KnowledgeVector:
        try:
            log_info(f"[KNOWLEDGE_COMPRESSOR] Kompresja {len(conversations)} rozmów")

            dominant_themes = await self._extract_dominant_themes(conversations)
            emotional_signature = await self._analyze_emotional_patterns(conversations)
            embedding = await self._generate_mini_embedding(conversations, dominant_themes)

            original_size = sum(len(str(c)) for c in conversations)
            compressed_size = len(embedding) * 4
            compression_ratio = (original_size / compressed_size) if compressed_size else 0.0
            temporal_weight = self._calculate_temporal_weight(conversations)
            confidence_score = await self._calculate_compression_confidence(conversations, embedding, dominant_themes)

            vector_id = hashlib.md5(f"{user_id}_{time.time()}".encode()).hexdigest()[:12]
            kv = KnowledgeVector(
                vector_id=vector_id,
                dimensions=len(embedding),
                embedding=embedding,
                compression_ratio=compression_ratio,
                source_conversations=[str(c.get("id", i)) for i, c in enumerate(conversations)],
                dominant_themes=dominant_themes,
                emotional_signature=emotional_signature,
                temporal_weight=temporal_weight,
                confidence_score=confidence_score,
                created_at=_now(),
                last_updated=_now(),
                usage_count=0
            )

            async with self._lock:
                self.knowledge_vectors[vector_id] = kv
                self._update_comp_stats(compression_ratio)

            log_info(f"[KNOWLEDGE_COMPRESSOR] Wektor {vector_id} ratio={compression_ratio:.1f}x conf={confidence_score:.2f}")
            return kv

        except Exception as e:
            log_error(f"[KNOWLEDGE_COMPRESSOR] Błąd kompresji: {e}")
            raise

    async def detect_thinking_patterns(self, user_id: str) -> List[ThinkingPattern]:
        try:
            episodes = await self.hierarchical_memory.search_episodes(query="", user_id=user_id, limit=50)
            if len(episodes) < 10:
                log_warning("[KNOWLEDGE_COMPRESSOR] Za mało danych")
                return []

            context_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
            for ep in episodes:
                topic = ep.get("context", {}).get("topic", "general")
                context_groups[topic].append(ep)

            patterns: List[ThinkingPattern] = []
            for topic, eps in context_groups.items():
                if len(eps) < 3:
                    continue
                p = await self._analyze_thinking_pattern(topic, eps, user_id)
                if p:
                    patterns.append(p)

            async with self._lock:
                for p in patterns:
                    self.thinking_patterns[p.pattern_id] = p
                self.compression_stats["patterns_discovered"] += len(patterns)

            log_info(f"[KNOWLEDGE_COMPRESSOR] Wzorców: {len(patterns)}")
            return patterns

        except Exception as e:
            log_error(f"[KNOWLEDGE_COMPRESSOR] Błąd detekcji: {e}")
            return []

    async def synthesize_new_knowledge(self, vectors: List[KnowledgeVector], creativity: Optional[float] = None) -> SyntheticMemory:
        creativity = 0.7 if creativity is None else max(0.0, min(1.0, creativity))
        try:
            combined_embedding = self._combine_embeddings(vectors)
            all_themes = [t for v in vectors for t in v.dominant_themes]
            synthesized_themes = await self._synthesize_themes(all_themes, creativity)
            synthetic_content = await self._generate_synthetic_content(vectors, synthesized_themes, creativity)

            abstraction_level = self._calculate_abstraction_level(vectors)
            generalization_power = self._calculate_generalization_power(vectors)
            predictive_value = await self._estimate_predictive_value(synthetic_content)
            applicable_contexts = await self._identify_applicable_contexts(synthetic_content, synthesized_themes)

            memory_id = hashlib.md5(f"synthesis_{time.time()}".encode()).hexdigest()[:12]
            sm = SyntheticMemory(
                memory_id=memory_id,
                compressed_content=synthetic_content,
                abstraction_level=abstraction_level,
                generalization_power=generalization_power,
                applicable_contexts=applicable_contexts,
                derived_from=[v.vector_id for v in vectors],
                predictive_value=predictive_value
            )

            async with self._lock:
                self.synthetic_memories[memory_id] = sm
                self.compression_stats["synthetic_memories_created"] += 1

            log_info(f"[KNOWLEDGE_COMPRESSOR] Synthesis {memory_id}")
            return sm

        except Exception as e:
            log_error(f"[KNOWLEDGE_COMPRESSOR] Błąd syntezy: {e}")
            raise

    async def get_compression_report(self) -> Dict[str, Any]:
        async with self._lock:
            kv = self.knowledge_vectors
            tp = self.thinking_patterns
            sm = self.synthetic_memories
            return {
                "stats": dict(self.compression_stats),
                "knowledge_vectors": {
                    "count": len(kv),
                    "avg_confidence": (sum(v.confidence_score for v in kv.values()) / len(kv)) if kv else 0.0,
                    "total_dimensions": sum(v.dimensions for v in kv.values()),
                    "avg_compression_ratio": (sum(v.compression_ratio for v in kv.values()) / len(kv)) if kv else 0.0
                },
                "thinking_patterns": {
                    "count": len(tp),
                    "pattern_types": sorted(set(p.pattern_type for p in tp.values())),
                    "avg_success_rate": (sum(p.success_rate for p in tp.values()) / len(tp)) if tp else 0.0
                },
                "synthetic_memories": {
                    "count": len(sm),
                    "avg_abstraction": (sum(m.abstraction_level for m in sm.values()) / len(sm)) if sm else 0.0,
                    "avg_generalization": (sum(m.generalization_power for m in sm.values()) / len(sm)) if sm else 0.0
                }
            }

    # -------------------- Prywatne metody --------------------

    async def _extract_dominant_themes(self, conversations: List[Dict[str, Any]]) -> List[str]:
        combined = "\n".join((c.get("content", "") + " " + str(c.get("context", ""))) for c in conversations)
        combined = combined[:MAX_PROMPT_CHARS]
        prompt = (
            "Wydobądź 5–8 dominujących tematów z treści. Zwróć po jednym na linię.\n\n"
            f"{combined}"
        )
        try:
            text = await _chat_text(self.llm_client, [
                {"role": "system", "content": "Jesteś analitykiem tematów."},
                {"role": "user", "content": prompt}
            ])
            themes = [t.strip() for t in text.splitlines() if t.strip()]
            return themes[:self.THEMES_MAX] if themes else ["temat_ogólny"]
        except Exception as e:
            log_warning(f"_extract_dominant_themes fallback: {e}")
            return ["temat_ogólny"]

    async def _analyze_emotional_patterns(self, conversations: List[Dict[str, Any]]) -> Dict[str, float]:
        emotions = ["radość", "smutek", "gniew", "strach", "zaskoczenie", "pogarda", "neutralność"]
        score = {e: 0.0 for e in emotions}
        keywords = {
            "radość": ["radość", "szczęś", "dobr", "super", "świetn", "uśmiech"],
            "smutek": ["smut", "żal", "przykro", "boles", "łz"],
            "gniew": ["gniew", "zły", "wkurz", "irytac", "frustrac"],
            "strach": ["strach", "lęk", "niepok", "obaw", "przeraż"],
            "zaskoczenie": ["zask", "wow", "niesamow"],
            "pogarda": ["pogard", "obrzydz", "wstręt", "nienawi"],
            "neutralność": ["ok", "dobrze", "normaln", "standard"]
        }
        total = 0
        for c in conversations:
            words = c.get("content", "").lower().split()
            total += len(words)
            for emo, kws in keywords.items():
                cnt = sum(1 for w in words if any(kw in w for kw in kws))
                score[emo] += cnt
        if total > 0:
            for emo in score:
                score[emo] = score[emo] / total
        return score

    async def _generate_mini_embedding(self, conversations: List[Dict[str, Any]], themes: List[str]) -> List[float]:
        text = "Tematy: " + ", ".join(themes) + "\n"
        for i, c in enumerate(conversations[: self.SAMPLE_CONV]):
            text += f"Fragment {i+1}: {c.get('content', '')[:self.MAX_FRAGMENT]}\n"
        text = text[:MAX_PROMPT_CHARS]

        prompt = (
            "Wygeneruj listę 128 liczb float w przedziale [-1,1], po przecinku, bez innych znaków:\n\n"
            f"{text}"
        )
        try:
            resp = await _chat_text(self.llm_client, [
                {"role": "system", "content": "Jesteś algorytmem embeddingu."},
                {"role": "user", "content": prompt}
            ])
            nums: List[float] = []
            for piece in resp.replace("\n", ",").split(","):
                piece = piece.strip()
                if not piece:
                    continue
                try:
                    nums.append(_clamp(float(piece)))
                except:
                    nums.append(0.0)
            if len(nums) < self.VECTOR_DIM:
                nums += [0.0] * (self.VECTOR_DIM - len(nums))
            nums = nums[: self.VECTOR_DIM]
            mag = math.sqrt(sum(x * x for x in nums))
            return [x / mag for x in nums] if mag else nums
        except Exception as e:
            log_warning(f"_generate_mini_embedding fallback: {e}")
            rv = [random.uniform(-1, 1) for _ in range(self.VECTOR_DIM)]
            mag = math.sqrt(sum(x * x for x in rv))
            return [x / mag for x in rv] if mag else rv

    def _calculate_temporal_weight(self, conversations: List[Dict[str, Any]]) -> float:
        now = _now()
        weights = []
        for c in conversations:
            ts = c.get("timestamp")
            try:
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts)
                if ts:
                    days = max(0.0, (now - ts).days)
                    weights.append(math.exp(-days / 30.0))
            except:
                continue
        return (sum(weights) / len(weights)) if weights else 1.0

    async def _calculate_compression_confidence(self, conversations: List[Dict[str, Any]], embedding: List[float], themes: List[str]) -> float:
        conf = 0.0
        conf += min(len(conversations) / 20.0, 0.3)
        conf += min(len(themes) / 10.0, 0.2)
        non_zero = sum(1 for x in embedding if abs(x) > 0.01)
        conf += min(non_zero / len(embedding), 0.3)
        total_len = sum(len(str(c)) for c in conversations)
        conf += min(total_len / 10000.0, 0.2)
        return min(conf, 1.0)

    def _combine_embeddings(self, vectors: List[KnowledgeVector]) -> List[float]:
        if not vectors:
            return [0.0] * self.VECTOR_DIM
        total_w = sum(v.confidence_score for v in vectors) or len(vectors)
        out = [0.0] * self.VECTOR_DIM
        for v in vectors:
            w = v.confidence_score / total_w
            for i, val in enumerate(v.embedding):
                out[i] += w * val
        mag = math.sqrt(sum(x * x for x in out))
        return [x / mag for x in out] if mag else out

    async def _synthesize_themes(self, themes: List[str], creativity: float) -> List[str]:
        uniq = list(dict.fromkeys(themes))  # zachowaj kolejność, usuń duplikaty
        if len(uniq) < 2:
            return uniq[:5]
        prompt = (
            f"Mając tematy: {', '.join(uniq[:10])}\n"
            f"Kreatywność: {creativity}\n"
            "Stwórz 3–5 nowych, praktycznych tematów łączących elementy powyższych. Zwróć po jednym na linię."
        )
        try:
            text = await _chat_text(self.llm_client, [
                {"role": "system", "content": "Jesteś syntezatorem tematów."},
                {"role": "user", "content": prompt}
            ])
            out = [t.strip() for t in text.splitlines() if t.strip()]
            return out[:5] if out else uniq[:5]
        except Exception as e:
            log_warning(f"_synthesize_themes fallback: {e}")
            return uniq[:5]

    async def _generate_synthetic_content(self, vectors: List[KnowledgeVector], themes: List[str], creativity: float) -> str:
        src = "\n".join([f"Tematy: {', '.join(v.dominant_themes[:3])}" for v in vectors[:5]])
        prompt = (
            f"Źródła:\n{src}\n\n"
            f"Nowe tematy: {', '.join(themes)}\n"
            f"Kreatywność: {creativity}\n"
            "Napisz 200–400 słów syntezy z praktycznymi implikacjami i przykładami. Bez wypełniaczy."
        )
        prompt = prompt[:MAX_PROMPT_CHARS]
        try:
            return await _chat_text(self.llm_client, [
                {"role": "system", "content": "Tworzysz zwartą, praktyczną syntezę."},
                {"role": "user", "content": prompt}
            ])
        except Exception as e:
            log_warning(f"_generate_synthetic_content fallback: {e}")
            return f"Synteza tematów: {', '.join(themes)}"

    def _calculate_abstraction_level(self, vectors: List[KnowledgeVector]) -> int:
        n = len(vectors)
        if n >= 5: return 5
        if n >= 3: return 4
        if n >= 2: return 3
        return 2

    def _calculate_generalization_power(self, vectors: List[KnowledgeVector]) -> float:
        if not vectors:
            return 0.0
        avg = sum(v.compression_ratio for v in vectors) / len(vectors)
        return min(avg / 100.0, 1.0)

    async def _estimate_predictive_value(self, content: str) -> float:
        indicators = ["wzorzec", "trend", "przewid", "prawdopodob", "powinien", "zasad", "reguł", "prawidłowo"]
        low = content.lower()
        hits = sum(1 for k in indicators if k in low)
        return min(hits / max(1, len(indicators)), 1.0)

    async def _identify_applicable_contexts(self, content: str, themes: List[str]) -> List[str]:
        prompt = (
            "Dla poniższej syntezy wypisz 3–5 konkretnych kontekstów zastosowań, po 1 na linię.\n\n"
            f"{content[:2000]}\n\n"
            f"Tematy: {', '.join(themes[:8])}"
        )
        try:
            text = await _chat_text(self.llm_client, [
                {"role": "system", "content": "Identyfikujesz praktyczne konteksty."},
                {"role": "user", "content": prompt[:MAX_PROMPT_CHARS]}
            ])
            ctx = [t.strip() for t in text.splitlines() if t.strip()]
            return ctx[:5] if ctx else ["kontekst_ogólny"]
        except Exception as e:
            log_warning(f"_identify_applicable_contexts fallback: {e}")
            return ["kontekst_ogólny"]

    def _update_comp_stats(self, ratio: float):
        s = self.compression_stats
        n1 = s["total_compressed"]
        s["total_compressed"] = n1 + 1
        s["compression_ratio_avg"] = (s["compression_ratio_avg"] * n1 + ratio) / (n1 + 1)


# --------------------------- Singleton ---------------------------

_knowledge_compressor: Optional[KnowledgeCompressor] = None

def get_knowledge_compressor() -> KnowledgeCompressor:
    global _knowledge_compressor
    if _knowledge_compressor is None:
        _knowledge_compressor = KnowledgeCompressor()
    return _knowledge_compressor
