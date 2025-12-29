"""
Future Context Predictor – wersja ulepszona
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
from enum import Enum
import hashlib
import math

from .config import *
from .llm import get_llm_client
from .memory import get_memory_manager
from .hierarchical_memory import get_hierarchical_memory
from .helpers import log_info, log_error, log_warning


# --------------------------- Stałe i pomocnicze ---------------------------

MAX_PROMPT_CHARS = 8000

# progi w jednym miejscu
THRESH_TREE = 0.40
THRESH_NODE_KEEP = 0.30
THRESH_PREPARE = 0.60
SIMILARITY_HIT = 0.70

MAX_PRED_DEPTH = 3
TOP_PRED_FOR_PREP = 3
CACHE_VALIDITY_H = 24
MAX_PREPS_PER_USER = 10


async def _chat_text(llm_client, messages) -> str:
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

class IntentionConfidence(Enum):
    VERY_LOW = 0.1
    LOW = 0.3
    MEDIUM = 0.5
    HIGH = 0.7
    VERY_HIGH = 0.9


class PredictionHorizon(Enum):
    IMMEDIATE = "immediate"
    SHORT_TERM = "short_term"
    MEDIUM_TERM = "medium_term"
    LONG_TERM = "long_term"


@dataclass
class IntentionNode:
    intention_id: str
    user_id: str
    predicted_query: str
    confidence: float
    horizon: PredictionHorizon
    parent_intention: Optional[str]
    child_intentions: List[str]
    context_triggers: List[str]
    preparation_data: Dict[str, Any]
    created_at: datetime
    activation_conditions: List[str]
    estimated_complexity: float
    domain: str
    emotional_valence: float


@dataclass
class PredictivePreparation:
    intention_id: str
    user_id: str
    prepared_content: str
    research_data: List[Dict[str, Any]]
    cached_responses: Dict[str, str]
    resource_links: List[str]
    preparation_confidence: float
    preparation_time: float
    validity_expires: datetime


@dataclass
class UserIntentionProfile:
    user_id: str
    common_patterns: List[str]
    topic_transitions: Dict[str, List[str]]
    temporal_patterns: Dict[str, Dict[str, float]]   # godzina -> {temat: p}
    curiosity_vectors: List[str]
    question_complexity_trend: float
    attention_span_estimate: float
    learning_trajectory: List[str]


# --------------------------- Predyktor ---------------------------

class FutureContextPredictor:
    """
    Przewidywanie intencji z proaktywnym przygotowaniem.
    Odporne na współbieżność. Raporty JSON-bezpieczne.
    """

    def __init__(self):
        self.llm_client = get_llm_client()
        self.memory = get_memory_manager()
        self.hierarchical_memory = get_hierarchical_memory()

        self.intention_trees: Dict[str, List[IntentionNode]] = defaultdict(list)  # user_id -> nodes
        self.user_profiles: Dict[str, UserIntentionProfile] = {}
        self.predictive_cache: Dict[str, PredictivePreparation] = {}
        self._intent_to_user: Dict[str, str] = {}  # intention_id -> user_id

        self.global_transition_patterns: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))

        self.prediction_stats = {
            "total_predictions": 0,
            "successful_predictions": 0,
            "cache_hits": 0,
            "proactive_preparations": 0,
            "accuracy_by_horizon": {h: {"correct": 0, "total": 0} for h in PredictionHorizon}
        }

        self._lock = asyncio.Lock()
        log_info("[FUTURE_PREDICTOR] Init OK")

    # -------------------- Public API --------------------

    async def predict_user_intentions(
        self,
        user_id: str,
        current_query: str,
        conversation_context: Optional[List[Dict[str, Any]]] = None,
        horizon: PredictionHorizon = PredictionHorizon.SHORT_TERM
    ) -> List[IntentionNode]:

        try:
            await self._update_user_profile(user_id, current_query, conversation_context or [])

            transition_patterns = await self._analyze_transition_patterns(user_id, current_query)
            predicted_queries = await self._generate_predicted_queries(
                user_id, current_query, conversation_context or [], horizon
            )

            nodes: List[IntentionNode] = []
            for pq in predicted_queries:
                conf = await self._calculate_prediction_confidence(
                    user_id, current_query, pq, transition_patterns
                )
                if conf >= THRESH_NODE_KEEP:
                    nid = hashlib.md5(f"{user_id}_{pq['query']}_{time.time()}".encode()).hexdigest()[:12]
                    node = IntentionNode(
                        intention_id=nid,
                        user_id=user_id,
                        predicted_query=pq["query"],
                        confidence=conf,
                        horizon=horizon,
                        parent_intention=None,
                        child_intentions=[],
                        context_triggers=pq.get("triggers", []),
                        preparation_data={},
                        created_at=_now(),
                        activation_conditions=pq.get("conditions", []),
                        estimated_complexity=float(pq.get("complexity", 0.5)),
                        domain=pq.get("domain", "general"),
                        emotional_valence=float(pq.get("emotional_valence", 0.0)),
                    )
                    nodes.append(node)

            nodes.sort(key=lambda x: x.confidence, reverse=True)

            async with self._lock:
                self.intention_trees[user_id].extend(nodes)
                self._clean_old_intentions_locked(user_id)
                self.prediction_stats["total_predictions"] += len(nodes)
                for n in nodes[:TOP_PRED_FOR_PREP]:
                    if n.confidence > THRESH_PREPARE:
                        # proaktywne przygotowanie poza lockiem – ale rejestr po
                        pass

            # przygotowania robimy równolegle po odblokowaniu
            prep_candidates = [n for n in nodes[:TOP_PRED_FOR_PREP] if n.confidence > THRESH_PREPARE]
            await asyncio.gather(*(self._proactive_preparation(n) for n in prep_candidates))

            return nodes

        except Exception as e:
            log_error(f"[FUTURE_PREDICTOR] Błąd predykcji: {e}")
            return []

    async def check_prediction_hit(self, user_id: str, actual_query: str) -> Optional[PredictivePreparation]:
        try:
            async with self._lock:
                intents = list(self.intention_trees.get(user_id, []))

            for it in intents:
                sim = await self._calculate_query_similarity(actual_query, it.predicted_query)
                if sim > SIMILARITY_HIT:
                    async with self._lock:
                        prep = self.predictive_cache.get(it.intention_id)
                        if prep and _now() < prep.validity_expires:
                            self.prediction_stats["successful_predictions"] += 1
                            self.prediction_stats["cache_hits"] += 1
                            hstats = self.prediction_stats["accuracy_by_horizon"][it.horizon]
                            hstats["correct"] += 1
                            hstats["total"] += 1
                            return prep

            # miss → zlicz total
            async with self._lock:
                for it in intents:
                    self.prediction_stats["accuracy_by_horizon"][it.horizon]["total"] += 1
            return None

        except Exception as e:
            log_error(f"[FUTURE_PREDICTOR] Błąd hit-check: {e}")
            return None

    async def build_intention_tree(self, user_id: str, root_query: str, max_depth: int = MAX_PRED_DEPTH) -> Dict[str, Any]:
        tree = {"root": {"query": root_query, "level": 0, "children": []}}
        try:
            await self._build_tree_recursive(user_id, root_query, tree["root"], 0, max_depth)
            return tree
        except Exception as e:
            log_error(f"[FUTURE_PREDICTOR] Błąd budowy drzewa: {e}")
            return tree

    async def get_prediction_report(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        async with self._lock:
            report = {
                "global_stats": {
                    **self.prediction_stats,
                    "accuracy_by_horizon": {
                        h.value: (
                            (v["correct"] / v["total"]) if v["total"] else 0.0
                        )
                        for h, v in self.prediction_stats["accuracy_by_horizon"].items()
                    }
                },
                "cache_size": len(self.predictive_cache),
                "active_users": len(self.intention_trees),
                "total_intentions": sum(len(v) for v in self.intention_trees.values())
            }
            if user_id and user_id in self.user_profiles:
                p = self.user_profiles[user_id]
                intents = sorted(self.intention_trees.get(user_id, []), key=lambda x: x.confidence, reverse=True)
                report["user_specific"] = {
                    "profile": {
                        "common_patterns": list(p.common_patterns),
                        "topic_transitions": dict(p.topic_transitions),
                        "complexity_trend": p.question_complexity_trend,
                        "attention_span": p.attention_span_estimate
                    },
                    "active_intentions": len(intents),
                    "top_predictions": [
                        {"query": it.predicted_query[:120], "confidence": it.confidence, "domain": it.domain}
                        for it in intents[:5]
                    ]
                }
            return report

    # -------------------- Prywatne metody --------------------

    async def _update_user_profile(self, user_id: str, current_query: str, conversation_context: List[Dict[str, Any]]):
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserIntentionProfile(
                user_id=user_id,
                common_patterns=[],
                topic_transitions={},
                temporal_patterns={},
                curiosity_vectors=[]
                ,
                question_complexity_trend=0.5,
                attention_span_estimate=5.0,
                learning_trajectory=[]
            )
        profile = self.user_profiles[user_id]
        await self._extract_patterns_from_query(profile, current_query)

        if conversation_context and len(conversation_context) > 1:
            await self._update_topic_transitions(profile, conversation_context)

        hour = str(_now().hour)
        topic = await self._extract_topic(current_query)
        if topic:
            if hour not in profile.temporal_patterns:
                profile.temporal_patterns[hour] = {}
            profile.temporal_patterns[hour][topic] = profile.temporal_patterns[hour].get(topic, 0.0) + 0.1

    async def _extract_patterns_from_query(self, profile: UserIntentionProfile, query: str):
        q = query.lower()
        for token in ["jak", "dlaczego", "co", "gdzie", "kiedy", "czy"]:
            if token in q and token not in profile.common_patterns:
                profile.common_patterns.append(token)
        for ind in ["ciekawi", "interesuje", "chciałbym wiedzieć", "zastanawiam się"]:
            if ind in q and ind not in profile.curiosity_vectors:
                profile.curiosity_vectors.append(ind)
        complexity = len(query.split()) / 20.0
        profile.question_complexity_trend = profile.question_complexity_trend * 0.8 + complexity * 0.2

    async def _extract_topic(self, text: str) -> Optional[str]:
        prompt = (
            "Zidentyfikuj główny temat w 1 słowie (np. technologia, nauka, biznes, psychologia). "
            "Zwróć dokładnie jedno słowo.\n\n"
            f"TEKST: {text[:600]}"
        )
        try:
            topic = await _chat_text(self.llm_client, [
                {"role": "system", "content": "Klasyfikator tematów. Odpowiadasz jednym słowem."},
                {"role": "user", "content": prompt}
            ])
            return topic.strip().split()[0].lower() if topic.strip() else None
        except:
            return None

    async def _update_topic_transitions(self, profile: UserIntentionProfile, conversation_context: List[Dict[str, Any]]):
        recent = []
        for msg in conversation_context[-5:]:
            if msg.get("role") == "user":
                t = await self._extract_topic(msg.get("content", ""))
                if t:
                    recent.append(t)
        for i in range(len(recent) - 1):
            a, b = recent[i], recent[i + 1]
            profile.topic_transitions.setdefault(a, [])
            if b not in profile.topic_transitions[a]:
                profile.topic_transitions[a].append(b)
            self.global_transition_patterns[a][b] += 0.1

    async def _analyze_transition_patterns(self, user_id: str, current_query: str) -> Dict[str, float]:
        topic = await self._extract_topic(current_query)
        if not topic:
            return {}
        patt: Dict[str, float] = {}
        profile = self.user_profiles.get(user_id)
        if profile and topic in profile.topic_transitions:
            for nxt in profile.topic_transitions[topic]:
                patt[nxt] = patt.get(nxt, 0.0) + 0.6
        if topic in self.global_transition_patterns:
            for nxt, w in self.global_transition_patterns[topic].items():
                patt[nxt] = patt.get(nxt, 0.0) + 0.4 * w
        tot = sum(patt.values())
        if tot:
            patt = {k: v / tot for k, v in patt.items()}
        return patt

    async def _generate_predicted_queries(
        self,
        user_id: str,
        current_query: str,
        conversation_context: List[Dict[str, Any]],
        horizon: PredictionHorizon
    ) -> List[Dict[str, Any]]:
        profile = self.user_profiles.get(user_id)
        ctx = {
            "current_query": current_query[:400],
            "user_patterns": profile.common_patterns if profile else [],
            "recent_topics": [m.get("content", "")[:80] for m in conversation_context[-3:]],
            "complexity_trend": profile.question_complexity_trend if profile else 0.5,
            "curiosity_vectors": profile.curiosity_vectors if profile else []
        }
        prompt = (
            "Wygeneruj 5–8 możliwych następnych zapytań użytkownika dla horyzontu "
            f"{horizon.value}. Zwróć JSON listę obiektów:\n"
            '{ "query": str, "triggers": [str], "conditions": [str], '
            '"complexity": float, "domain": str, "emotional_valence": float }\n\n'
            f"Kontekst:\n{json.dumps(ctx, ensure_ascii=False)[:MAX_PROMPT_CHARS]}"
        )
        try:
            text = await _chat_text(self.llm_client, [
                {"role": "system", "content": f"Generujesz prawdopodobne kolejne pytania ({horizon.value})."},
                {"role": "user", "content": prompt}
            ])
            try:
                data = json.loads(text)
                return data[:8] if isinstance(data, list) else []
            except json.JSONDecodeError:
                return self._fallback_parse_predictions(text)
        except Exception as e:
            log_warning(f"_generate_predicted_queries fallback: {e}")
            return []

    def _fallback_parse_predictions(self, response: str) -> List[Dict[str, Any]]:
        out = []
        for line in response.splitlines():
            line = line.strip()
            if line and "?" in line:
                out.append({
                    "query": line,
                    "triggers": ["followup"],
                    "conditions": ["natural_flow"],
                    "complexity": 0.5,
                    "domain": "general",
                    "emotional_valence": 0.0
                })
        return out[:5]

    async def _calculate_prediction_confidence(
        self, user_id: str, current_query: str, prediction: Dict[str, Any], transition_patterns: Dict[str, float]
    ) -> float:
        conf = 0.0
        topic = await self._extract_topic(prediction["query"])
        if topic and topic in transition_patterns:
            conf += 0.4 * transition_patterns[topic]

        profile = self.user_profiles.get(user_id)
        if profile:
            ql = prediction["query"].lower()
            if profile.common_patterns:
                matches = sum(1 for p in profile.common_patterns if p in ql)
                conf += min(matches / len(profile.common_patterns), 0.3)
            diff = abs(float(prediction.get("complexity", 0.5)) - profile.question_complexity_trend)
            conf += (1 - min(1.0, diff)) * 0.2

        triggers = prediction.get("triggers", [])
        cur = current_query.lower()
        conf += min(sum(1 for t in triggers if t.lower() in cur) * 0.1, 0.1)

        return min(conf, 1.0)

    def _clean_old_intentions_locked(self, user_id: str):
        cutoff = _now() - timedelta(hours=CACHE_VALIDITY_H)
        lst = [n for n in self.intention_trees[user_id] if n.created_at > cutoff]
        if len(lst) > 20:
            lst.sort(key=lambda x: x.confidence, reverse=True)
            lst = lst[:20]
        self.intention_trees[user_id] = lst

    async def _proactive_preparation(self, intention: IntentionNode):
        try:
            t0 = time.time()
            prepared = await self._prepare_response(intention.predicted_query, intention.domain)
            research = await self._gather_research_data(intention.predicted_query, intention.domain)
            links = await self._prepare_resource_links(intention.predicted_query, intention.domain)
            quality = await self._evaluate_preparation_quality(prepared, research, links)

            prep = PredictivePreparation(
                intention_id=intention.intention_id,
                user_id=intention.user_id,
                prepared_content=prepared,
                research_data=research,
                cached_responses={
                    "main": prepared,
                    "summary": prepared[:500] + ("..." if len(prepared) > 500 else "")
                },
                resource_links=links,
                preparation_confidence=quality,
                preparation_time=time.time() - t0,
                validity_expires=_now() + timedelta(hours=CACHE_VALIDITY_H)
            )

            async with self._lock:
                self.predictive_cache[intention.intention_id] = prep
                self._intent_to_user[intention.intention_id] = intention.user_id
                self._limit_cache_per_user_locked(intention.user_id)
                self.prediction_stats["proactive_preparations"] += 1

        except Exception as e:
            log_error(f"[FUTURE_PREDICTOR] Błąd przygotowania: {e}")

    async def _prepare_response(self, predicted_query: str, domain: str) -> str:
        prompt = (
            "Przygotuj rzeczową, praktyczną odpowiedź 300–600 słów z przykładami. "
            f"Domena: {domain}\n\nPytanie: {predicted_query}"
        )
        try:
            return await _chat_text(self.llm_client, [
                {"role": "system", "content": f"Asystent domenowy: {domain}."},
                {"role": "user", "content": prompt[:MAX_PROMPT_CHARS]}
            ])
        except Exception as e:
            return f"Błąd przygotowania odpowiedzi: {e}"

    async def _gather_research_data(self, query: str, domain: str) -> List[Dict[str, Any]]:
        # generuje strukturalne “fikcyjne ale realistyczne” wpisy z flagą is_fictional
        data: List[Dict[str, Any]] = []
        # akademickie
        data.append({
            "type": "academic_source",
            "title": f"Analiza aspektów '{query[:50]}' w domenie {domain}",
            "authors": "A. Kowalski, B. Nowak",
            "institution": "Uniwersytet Przykładowy",
            "year": "2023",
            "key_findings": "Ustalenia dot. skuteczności i ograniczeń.",
            "methodology": "Przegląd literatury + eksperymenty kontrolowane.",
            "implications": "Wskazówki dla praktyków.",
            "confidence": 0.8,
            "source_quality": "high",
            "is_fictional": True
        })
        # praktyczne
        data.append({
            "type": "practical_guide",
            "title": f"Przewodnik wdrożenia: {domain} → {query[:40]}",
            "difficulty_level": "średni",
            "estimated_time": "2–4h",
            "required_tools": "lista narzędzi",
            "step_by_step": "kroki 1..n",
            "common_mistakes": "omówienie błędów",
            "expected_results": "konkretne KPI",
            "next_steps": "ścieżka rozwoju",
            "confidence": 0.9,
            "actionability": "high",
            "is_fictional": True
        })
        # case study
        data.append({
            "type": "case_study",
            "name": "Case X",
            "context": "Środowisko Y",
            "initial_state": "Stan początkowy",
            "solution": "Opis rozwiązania",
            "implementation": "Kroki",
            "challenges": "Ryzyka",
            "results": "Rezultaty liczbowe",
            "lessons_learned": "Wnioski",
            "adaptation_potential": "Gdzie adaptować",
            "confidence": 0.85,
            "applicability": "medium",
            "is_fictional": True
        })
        # trend
        data.append({
            "type": "trend_analysis",
            "trend_name": "Trend Z",
            "current_state": "Stan obecny",
            "development_direction": "Kierunek",
            "driving_factors": "Czynniki",
            "barriers": "Bariery",
            "timeline": "Horyzont 12–24m",
            "implications": "Implikacje",
            "recommendations": "Rekomendacje",
            "alternative_scenarios": "Scenariusze",
            "confidence": 0.7,
            "time_horizon": "medium_term",
            "is_fictional": True
        })
        # scoring relevance
        for item in data:
            item["relevance_score"] = await self._calculate_research_relevance(item, query, domain)
        data.sort(key=lambda x: x.get("relevance_score", 0.0), reverse=True)
        return data[:10]

    async def _calculate_research_relevance(self, data_item: Dict[str, Any], query: str, domain: str) -> float:
        qwords = set(query.lower().split())
        title = (data_item.get("title") or data_item.get("name") or "").lower()
        tw = set(title.split())
        overlap = len(qwords & tw)
        rel = (overlap / max(1, len(qwords))) * 0.4
        st = data_item.get("type", "")
        rel += {"academic_source": 0.2, "practical_guide": 0.3, "case_study": 0.25, "trend_analysis": 0.15}.get(st, 0.0)
        rel += float(data_item.get("confidence", 0.5)) * 0.2
        detail_fields = ["key_findings", "step_by_step", "implementation", "results", "implications"]
        rel += (sum(1 for f in detail_fields if data_item.get(f)) / len(detail_fields)) * 0.2
        return min(rel, 1.0)

    async def _prepare_resource_links(self, query: str, domain: str) -> List[str]:
        # mapy znanych źródeł -> parametry wyszukiwania
        catalogs = {
            "documentation": ["developer.mozilla.org", "docs.python.org", "react.dev", "nodejs.org"],
            "tutorial": ["freecodecamp.org", "codecademy.com", "tutorialspoint.com", "w3schools.com"],
            "video": ["youtube.com", "pluralsight.com", "udemy.com", "coursera.org"],
            "community": ["stackoverflow.com", "dev.to", "reddit.com", "hashnode.com"],
            "courses": ["edx.org", "coursera.org", "udacity.com"]
        }
        qslug = query.lower().strip().replace(" ", "+")[:80]
        links: List[str] = []
        def build(host: str) -> str:
            if host.endswith("youtube.com"):
                return f"https://www.youtube.com/results?search_query={qslug}"
            if host.endswith("coursera.org"):
                return f"https://www.coursera.org/courses?query={qslug}"
            if host.endswith("stackoverflow.com"):
                return f"https://stackoverflow.com/search?q={qslug}"
            if host.endswith("github.com"):
                return f"https://github.com/search?q={qslug}&type=repositories"
            return f"https://{host}/search?q={qslug}"
        for typ in ["documentation", "tutorial", "video", "community", "courses"]:
            for host in catalogs.get(typ, [])[:2]:
                links.append(build(host))
        # deduplikacja
        out: List[str] = []
        seen = set()
        for l in links:
            if l not in seen:
                out.append(l); seen.add(l)
        return out[:10]

    async def _evaluate_preparation_quality(self, response: str, research_data: List[Dict[str, Any]], resources: List[str]) -> float:
        q = 0.0
        if len(response) > 200:
            q += 0.4
        q += min(len(research_data) * 0.2, 0.3)
        q += min(len(resources) * 0.1, 0.3)
        return min(q, 1.0)

    def _limit_cache_per_user_locked(self, user_id: str):
        # filtruj cache dla usera
        items: List[Tuple[str, PredictivePreparation]] = [
            (iid, prep) for iid, prep in self.predictive_cache.items() if prep.user_id == user_id
        ]
        if len(items) <= MAX_PREPS_PER_USER:
            return
        # usuń najstarsze
        items.sort(key=lambda kv: kv[1].validity_expires)
        to_drop = items[:-MAX_PREPS_PER_USER]
        for iid, _ in to_drop:
            self.predictive_cache.pop(iid, None)
            self._intent_to_user.pop(iid, None)

    async def _calculate_query_similarity(self, q1: str, q2: str) -> float:
        s1 = set(q1.lower().split())
        s2 = set(q2.lower().split())
        if not s1 or not s2:
            return 0.0
        inter = len(s1 & s2)
        union = len(s1 | s2)
        jacc = inter / union if union else 0.0
        len_sim = 1 - abs(len(q1) - len(q2)) / max(len(q1), len(q2))
        return 0.7 * jacc + 0.3 * len_sim

    async def _build_tree_recursive(self, user_id: str, current_query: str, node: Dict[str, Any], depth: int, max_depth: int):
        if depth >= max_depth:
            return
        preds = await self._generate_predicted_queries(user_id, current_query, [], PredictionHorizon.IMMEDIATE)
        for p in preds[:3]:
            conf = await self._calculate_prediction_confidence(user_id, current_query, p, {})
            if conf > THRESH_TREE:
                child = {
                    "query": p["query"],
                    "level": depth + 1,
                    "confidence": conf,
                    "domain": p.get("domain", "general"),
                    "children": []
                }
                node["children"].append(child)
                await self._build_tree_recursive(user_id, p["query"], child, depth + 1, max_depth)


# --------------------------- Singleton + wygodny wrapper ---------------------------

_future_predictor: Optional[FutureContextPredictor] = None

def get_future_predictor() -> FutureContextPredictor:
    global _future_predictor
    if _future_predictor is None:
        _future_predictor = FutureContextPredictor()
    return _future_predictor


async def predict_next_queries(
    user_id: str,
    current_query: str,
    context: Optional[List[Dict[str, Any]]] = None,
    horizon: str = "short_term"
) -> List[Dict[str, Any]]:
    predictor = get_future_predictor()
    try:
        horizon_enum = PredictionHorizon(horizon)
    except ValueError:
        horizon_enum = PredictionHorizon.SHORT_TERM
    intents = await predictor.predict_user_intentions(user_id, current_query, context or [], horizon_enum)
    return [{
        "query": it.predicted_query,
        "confidence": it.confidence,
        "domain": it.domain,
        "complexity": it.estimated_complexity,
        "triggers": it.context_triggers
    } for it in intents]