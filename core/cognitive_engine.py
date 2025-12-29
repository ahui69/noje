#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧠 ZAAWANSOWANY SILNIK KOGNITYWNY MRD - GŁÓWNY ORCHESTRATOR
===========================================================

Implementacja prawdziwego, zaawansowanego silnika kognitywnego z pełną integracją
wszystkich 5 systemów kognitywnych i kompletną logiką przetwarzania.

Autor: Zaawansowany System Kognitywny ahui69
Data: 15 października 2025
"""

import asyncio
import json
import os
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import asdict

# Podstawowe importy systemowe
from .config import *
from .llm import call_llm, call_llm_stream
from .memory import memory_manager
from .hierarchical_memory import hierarchical_memory_manager
from .helpers import log_info, log_error, log_warning
from .tools_registry import get_tool_by_name

# Import wszystkich zaawansowanych systemów kognitywnych
from .advanced_cognitive_engine import (
    get_advanced_cognitive_engine, 
    CognitiveMode, 
    CognitiveResult,
    process_with_full_cognition
)

# Import systemu pamięci hierarchicznej (fallback)
try:
    from .hierarchical_memory import (
        get_hierarchical_memory_system,
        enhance_memory_with_hierarchy,
        get_hierarchical_context,
        predict_user_next_action,
        get_user_comprehensive_profile
    )
    HIERARCHICAL_MEMORY_AVAILABLE = True
    log_info("[COGNITIVE_ENGINE] ✅ Hierarchical Memory System loaded")
except ImportError as e:
    log_warning(f"[COGNITIVE_ENGINE] Hierarchical Memory System not available: {e}")
    HIERARCHICAL_MEMORY_AVAILABLE = False

# Import fast path handlers (zachowujemy dla kompatybilności)
try:
    from .intent_dispatcher import FAST_PATH_HANDLERS
    FAST_PATH_AVAILABLE = True
    log_info("[COGNITIVE_ENGINE] ✅ Fast Path Handlers loaded")
except ImportError as e:
    log_warning(f"[COGNITIVE_ENGINE] Fast Path Handlers not available: {e}")
    FAST_PATH_HANDLERS = []
    FAST_PATH_AVAILABLE = False

# Import badań sieciowych
try:
    from .research import autonauka
    WEB_RESEARCH_AVAILABLE = True
    log_info("[COGNITIVE_ENGINE] ✅ Web Research System loaded")
except ImportError as e:
    log_warning(f"[COGNITIVE_ENGINE] Web Research System not available: {e}")
    WEB_RESEARCH_AVAILABLE = False

# Import tradycyjnych systemów (fallback)
try:
    from .memory import psy_observe_text, ltm_search_hybrid, stm_get_context, psy_tune
    from .user_model import user_model_manager
    LEGACY_SYSTEMS_AVAILABLE = True
    log_info("[COGNITIVE_ENGINE] ✅ Legacy Systems loaded for fallback")
except ImportError as e:
    log_warning(f"[COGNITIVE_ENGINE] Legacy Systems not available: {e}")
    LEGACY_SYSTEMS_AVAILABLE = False

class CognitiveEngine:
    """
    🧠 ZAAWANSOWANY SILNIK KOGNITYWNY MRD
    
    Prawdziwy, zaawansowany orchestrator łączący wszystkie systemy kognitywne:
    - 5 systemów kognitywnych w pełnej integracji
    - Adaptacyjne tryby przetwarzania 
    - Real-time metrics i optimization
    - Hierarchical memory integration
    - Fallback systems dla kompatybilności
    """
    
    def __init__(self):
        self.advanced_engine = get_advanced_cognitive_engine()
        self.memory = memory_manager
        self.hierarchical_memory = hierarchical_memory_manager
        
        try:
            self.web_confidence_threshold = float(os.getenv("WEB_RESEARCH_CONFIDENCE_THRESHOLD", "0.55"))
        except (TypeError, ValueError):
            self.web_confidence_threshold = 0.55
        self.web_research_keywords = [
            "sprawdź", "sprawdz", "wyszukaj", "szukaj", "poszukaj", "znajdź", "znajdz",
            "znajdź mi", "dowiedz się", "dowiedz sie", "zobacz w sieci", "w internecie",
            "w necie", "google", "wygoogluj", "autonauka", "web search", "sprawdź wynik",
            "sprawdz wynik", "przeszukaj", "ucz się", "ucz sie"
        ]
        self.web_research_tool_names = {"autonauka", "web_learn", "web_search"}

        # Metryki wydajności
        self.performance_stats = {
            "total_requests": 0,
            "advanced_engine_usage": 0,
            "fallback_usage": 0,
            "avg_processing_time": 0.0,
            "fast_path_hits": 0
        }
        
        log_info("[COGNITIVE_ENGINE] Zaawansowany silnik kognitywny zainicjalizowany")
    
    async def process_message(self, user_id: str, messages: List[Dict[str, Any]], req: Any) -> Dict[str, Any]:
        """
        Główna funkcja przetwarzania wiadomości z pełną kognicją
        
        Args:
            user_id: ID użytkownika
            messages: Historia wiadomości
            req: Request object
            
        Returns:
            Dict: Wynik przetwarzania z answer, sources, metadata
        """
        
        start_time = time.time()
        self.performance_stats["total_requests"] += 1
        
        try:
            # Wydobądź ostatnią wiadomość użytkownika
            last_user_msg = self._extract_last_user_message(messages)
            if not last_user_msg:
                return self._create_empty_response()
            
            log_info(f"[COGNITIVE_ENGINE] Przetwarzanie: {last_user_msg[:60]}...")
            
            # ETAP 1: Fast Path Check (zachowujemy dla kompatybilności)
            fast_path_result = await self._try_fast_path(last_user_msg, req)
            if fast_path_result:
                self.performance_stats["fast_path_hits"] += 1
                return fast_path_result
            
            # ETAP 1.5: 🔥 TOOL SELECTION & EXECUTION - AI wybiera które endpointy użyć (JAK CHATGPT!)
            tool_results = await self._analyze_and_execute_tools(last_user_msg, messages, user_id)
            
            # ETAP 2: Określ tryb kognitywny na podstawie wiadomości
            cognitive_mode = await self._determine_cognitive_mode(last_user_msg, user_id, messages)
            
            # ETAP 3: Przygotuj kontekst konwersacji + wyniki tools
            conversation_context = await self._prepare_conversation_context(messages, user_id)
            
            # Dodaj wyniki tools do kontekstu
            if tool_results and tool_results.get("execution"):
                conversation_context["tool_results"] = tool_results
            
            # ETAP 4: Przetwarzanie przez zaawansowany silnik kognitywny
            try:
                log_info(f"[COGNITIVE_ENGINE] Używam zaawansowanego silnika w trybie: {cognitive_mode.value}")
                
                cognitive_result = await self.advanced_engine.process_message(
                    user_message=last_user_msg,
                    user_id=user_id,
                    conversation_context=conversation_context,
                    cognitive_mode=cognitive_mode,
                    enable_prediction=True
                )
                
                self.performance_stats["advanced_engine_usage"] += 1
                
                # Konwertuj na format API
                result = await self._convert_cognitive_result_to_api_format(
                    cognitive_result, last_user_msg, req, tool_results
                )
                
            except Exception as e:
                log_error(f"[COGNITIVE_ENGINE] Zaawansowany silnik failed: {e}")
                
                # FALLBACK: Użyj systemów legacy
                result = await self._fallback_processing(
                    last_user_msg, user_id, messages, req
                )
                self.performance_stats["fallback_usage"] += 1
            
            # ETAP 5: Dodaj wyniki tools do odpowiedzi (JAK CHATGPT!)
            if tool_results:
                if "metadata" not in result:
                    result["metadata"] = {}
                
                result["metadata"]["tools_used"] = tool_results.get("tools_used", [])
                result["metadata"]["tool_plan"] = tool_results.get("plan", [])
                result["metadata"]["tool_execution"] = tool_results.get("execution", [])
                result["metadata"]["tool_summary"] = tool_results.get("summary", "")
                result["metadata"]["tool_reasoning"] = tool_results.get("reasoning")
                result["metadata"]["tool_confidence"] = tool_results.get("confidence")
                
                # Dodaj info o tools do odpowiedzi
                executed_tools = tool_results.get("tools_used", [])
                if executed_tools:
                    tools_info = f"\n\n🔧 **Użyte narzędzia**: {', '.join(executed_tools)}\n"
                    if tool_results.get("summary"):
                        tools_info += f"📊 {tool_results['summary']}"
                    result["answer"] = result.get("answer", "") + tools_info
            
            # ETAP 6: Aktualizuj statystyki
            processing_time = time.time() - start_time
            await self._update_performance_stats(processing_time)
            
            # Dodaj processing time do metadanych
            if "metadata" not in result:
                result["metadata"] = {}
            result["metadata"]["processing_time"] = processing_time
            result["metadata"]["cognitive_engine_version"] = "advanced_v2.0"
            
            log_info(f"[COGNITIVE_ENGINE] Przetwarzanie zakończone: {processing_time:.2f}s")
            return result
            
        except Exception as e:
            log_error(f"[COGNITIVE_ENGINE] Krytyczny błąd przetwarzania: {e}")
            return self._create_error_response(str(e))
    
    def _extract_last_user_message(self, messages: List[Dict[str, Any]]) -> str:
        """Wydobądź ostatnią wiadomość użytkownika"""
        for msg in reversed(messages):
            if msg.get('role') == 'user' and msg.get('content'):
                return msg['content'].strip()
        return ""
    
    async def _try_fast_path(self, message: str, req: Any) -> Optional[Dict[str, Any]]:
        """Sprawdź fast path handlers"""
        
        if not FAST_PATH_AVAILABLE:
            return None
        
        for handler in FAST_PATH_HANDLERS:
            try:
                result = await handler(message, req)
                if result is not None:
                    log_info(f"[COGNITIVE_ENGINE] ⚡ Fast Path HIT: {handler.__name__}")
                    return {
                        "answer": result,
                        "sources": [],
                        "metadata": {
                            "source": "fast_path",
                            "handler": handler.__name__
                        }
                    }
            except Exception as e:
                log_warning(f"[COGNITIVE_ENGINE] Fast path handler {handler.__name__} failed: {e}")
        
        return None
    
    async def _determine_cognitive_mode(
        self, 
        message: str, 
        user_id: str,
        messages: List[Dict[str, Any]]
    ) -> CognitiveMode:
        """Określ optymalny tryb kognitywny"""
        
        # Bazowe mapowanie na podstawie charakterystyk wiadomości
        message_lower = message.lower()
        
        # Tryb FULL_COGNITIVE dla złożonych zapytań
        complex_indicators = [
            "wyjaśnij", "przeanalizuj", "porównaj", "oceń", "co sądzisz",
            "jak myślisz", "dlaczego", "filozofia", "etyka", "znaczenie"
        ]
        
        if any(indicator in message_lower for indicator in complex_indicators):
            return CognitiveMode.FULL_COGNITIVE
        
        # Tryb MULTI_AGENT dla kontrowersyjnych tematów
        controversial_topics = [
            "polityka", "religia", "kontrowersj", "spór", "konflikt",
            "debata", "argument", "przeciw", "za i przeciw"
        ]
        
        if any(topic in message_lower for topic in controversial_topics):
            return CognitiveMode.MULTI_AGENT
        
        # Tryb PREDICTIVE dla zapytań o przyszłość
        future_indicators = [
            "będzie", "przyszłość", "przewiduj", "trend", "rozwój",
            "co dalej", "następn", "prognoza"
        ]
        
        if any(indicator in message_lower for indicator in future_indicators):
            return CognitiveMode.PREDICTIVE
        
        # Tryb ADVANCED dla długich konwersacji
        if len(messages) > 10:
            return CognitiveMode.ADVANCED
        
        # Domyślnie ENHANCED
        return CognitiveMode.ENHANCED
    
    async def _prepare_conversation_context(
        self, 
        messages: List[Dict[str, Any]], 
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Przygotuj kontekst konwersacji"""
        
        # Ostatnie 10 wiadomości z odpowiednim formatowaniem
        context = []
        for msg in messages[-10:]:
            if msg.get('role') in ['user', 'assistant'] and msg.get('content'):
                context.append({
                    "role": msg['role'],
                    "content": msg['content'],
                    "timestamp": msg.get('timestamp', datetime.now().isoformat())
                })
        
        # Dodaj kontekst z pamięci hierarchicznej jeśli dostępny
        if HIERARCHICAL_MEMORY_AVAILABLE:
            try:
                # Pobranie dodatkowego kontekstu z pamięci
                memory_context = get_hierarchical_context(
                    query=messages[-1].get('content', '') if messages else '',
                    user_id=user_id,
                    max_size=2000
                )
                
                # Dodaj episodic memories jako kontekst
                episodes = memory_context.get('episodic_memories', [])
                for episode in episodes[:3]:  # Top 3 episodes
                    context.append({
                        "role": "memory",
                        "content": episode.get('summary', ''),
                        "timestamp": episode.get('timestamp', ''),
                        "type": "episodic_memory"
                    })
                
            except Exception as e:
                log_warning(f"[COGNITIVE_ENGINE] Nie można pobrać kontekstu hierarchicznego: {e}")
        
        return context
    
    def _should_trigger_web_research(
        self,
        message: str,
        cognitive_result: CognitiveResult,
        tool_results: Optional[Dict[str, Any]]
    ) -> Tuple[bool, str]:
        """Decyduje, czy należy uruchomić web research."""

        if not message:
            return False, "no_message"

        normalized = message.strip().lower()
        if len(normalized) < 4:
            return False, "message_too_short"

        executed_tools: List[str] = []
        if tool_results:
            executed_tools = [
                str(tool).lower()
                for tool in tool_results.get("tools_used", [])
                if isinstance(tool, str)
            ]

            if not executed_tools and tool_results.get("execution"):
                executed_tools = [
                    str(entry.get("tool", "")).lower()
                    for entry in tool_results.get("execution", [])
                    if entry.get("tool")
                ]

        if any(name in self.web_research_tool_names for name in executed_tools):
            return False, "tool_already_executed"

        if any(keyword in normalized for keyword in self.web_research_keywords):
            return True, "explicit_request"

        confidence = getattr(cognitive_result, "confidence_score", None)
        if confidence is not None and confidence < self.web_confidence_threshold:
            return True, "low_confidence"

        return False, "confidence_ok"

    async def _convert_cognitive_result_to_api_format(
        self,
        cognitive_result: CognitiveResult,
        original_message: str,
        req: Any,
        tool_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Konwertuj wynik kognitywny na format API"""
        
        # Przygotuj źródła
        sources = []

        if cognitive_result.compressed_knowledge.get('research_sources'):
            sources.extend(cognitive_result.compressed_knowledge['research_sources'])

        should_fetch, trigger_reason = self._should_trigger_web_research(
            original_message, cognitive_result, tool_results
        )

        web_research_metadata = {
            "attempted": False,
            "status": "skipped",
            "trigger": trigger_reason,
            "confidence": getattr(cognitive_result, "confidence_score", None),
            "threshold": self.web_confidence_threshold
        }

        if should_fetch and WEB_RESEARCH_AVAILABLE:
            try:
                web_result = await autonauka(original_message, topk=3, user_id="system")
                web_research_metadata["attempted"] = True

                if web_result and isinstance(web_result, dict):
                    web_sources = web_result.get("sources") or web_result.get("citations") or []
                    if web_sources:
                        sources.extend(web_sources)
                        web_research_metadata["status"] = "success"
                        web_research_metadata["source_count"] = web_result.get("source_count", len(web_sources))
                    else:
                        web_research_metadata["status"] = "empty"
                else:
                    web_research_metadata["status"] = "empty"
            except Exception as e:
                web_research_metadata["attempted"] = True
                web_research_metadata["status"] = "error"
                web_research_metadata["error"] = str(e)
                log_warning(f"[COGNITIVE_ENGINE] Web research dla sources failed: {e}")
        elif should_fetch:
            web_research_metadata["status"] = "unavailable"
        
        # Przygotuj rozszerzone metadane
        metadata = {
            "source": "advanced_cognitive_engine",
            "cognitive_mode": "advanced",
            "processing_stages": list(cognitive_result.processing_metrics.keys()),
            "confidence_score": cognitive_result.confidence_score,
            "originality_score": cognitive_result.originality_score,
            "total_processing_time": cognitive_result.total_processing_time,
            
            # Szczegóły systemów kognitywnych
            "reflection_insights_count": len(cognitive_result.reflection_insights),
            "agent_perspectives_count": len(cognitive_result.agent_perspectives),
            "future_predictions_count": len(cognitive_result.future_predictions),
            "inner_language_compression": cognitive_result.inner_thought.get('compression_level', 0),
            "knowledge_vectors_used": len(cognitive_result.compressed_knowledge.get('knowledge_vectors', [])),
            
            # Request info
            "request_host": str(req.client.host) if req and hasattr(req, 'client') else "unknown",
            "timestamp": datetime.now().isoformat()
        }
        
        # Dodaj szczegółowe metryki jeśli są dostępne
        if cognitive_result.processing_metrics:
            metadata["stage_timings"] = cognitive_result.processing_metrics
        
        # Dodaj insights z refleksji jako dodatkowe info
        if cognitive_result.reflection_insights:
            metadata["reflection_summary"] = [
                insight.get('improvement_type', 'general') 
                for insight in cognitive_result.reflection_insights[:3]
            ]
        
        # Dodaj predykcje jako sugestie
        if cognitive_result.future_predictions:
            metadata["predicted_follow_ups"] = [
                pred.get('query', '')[:100] 
                for pred in cognitive_result.future_predictions[:3]
            ]

        metadata["web_research"] = web_research_metadata
        
        return {
            "answer": cognitive_result.primary_response,
            "sources": sources,
            "metadata": metadata
        }
    
    async def _fallback_processing(
        self,
        message: str,
        user_id: str,
        messages: List[Dict[str, Any]],
        req: Any
    ) -> Dict[str, Any]:
        """Fallback przetwarzanie używając legacy systems"""
        
        log_warning("[COGNITIVE_ENGINE] Używam fallback processing")
        
        try:
            if LEGACY_SYSTEMS_AVAILABLE:
                # Podstawowa obserwacja psychologiczna
                psy_observe_text(user_id, message)
                
                # Wyszukiwanie w pamięci
                memory_results = ltm_search_hybrid(message, limit=5)
                memory_context = "\n".join([
                    f"- {item.get('text', '')}" 
                    for item in memory_results[:3]
                ]) if memory_results else ""
                
                # Pobierz parametry strojenia
                tuned_params = psy_tune()
                
                # Przygotuj kontekst konwersacji
                stm_history = stm_get_context(user_id, limit=10)
                
                # Podstawowy prompt
                from .config import MORDZIX_SYSTEM_PROMPT
                system_prompt = tuned_params.get("persona_prompt", MORDZIX_SYSTEM_PROMPT)
                if memory_context:
                    system_prompt += f"\n\nKontekst z pamięci:\n{memory_context}"
                
                # LLM messages
                llm_messages = [
                    {"role": "system", "content": system_prompt}
                ] + stm_history + messages
                
                # Wywołanie LLM (synchroniczne, nie async)
                from .llm import call_llm
                response = call_llm(llm_messages, **tuned_params)
                
                return {
                    "answer": response,
                    "sources": [],
                    "metadata": {
                        "source": "fallback_legacy",
                        "memory_context_used": bool(memory_context),
                        "processing_mode": "basic"
                    }
                }
            
            else:
                # Ostateczny fallback - prosty LLM call
                from .config import MORDZIX_SYSTEM_PROMPT
                simple_response = call_llm([
                    {"role": "system", "content": MORDZIX_SYSTEM_PROMPT},
                    {"role": "user", "content": message}
                ])
                
                return {
                    "answer": simple_response,
                    "sources": [],
                    "metadata": {
                        "source": "simple_fallback",
                        "processing_mode": "minimal"
                    }
                }
                
        except Exception as e:
            log_error(f"[COGNITIVE_ENGINE] Fallback processing failed: {e}")
            return self._create_error_response(f"Fallback error: {e}")
    
    async def _update_performance_stats(self, processing_time: float):
        """Aktualizuj statystyki wydajności"""
        
        # Średni czas przetwarzania
        current_avg = self.performance_stats["avg_processing_time"]
        total_requests = self.performance_stats["total_requests"]
        
        self.performance_stats["avg_processing_time"] = (
            (current_avg * (total_requests - 1) + processing_time) / total_requests
        )
    
    async def _analyze_and_execute_tools(
        self, 
        message: str, 
        conversation_history: List[Dict[str, Any]], 
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        🔥 TOOL SELECTION & EXECUTION - Jak ChatGPT wybiera tools!
        
        1. LLM analizuje wiadomość i wybiera odpowiednie tools z 121 dostępnych
        2. Wykonuje wybrane tools (wywołuje endpointy)
        3. Zwraca wyniki do wplecenia w odpowiedź
        """
        try:
            from .intent_dispatcher import analyze_intent_and_select_tools, execute_selected_tools
            
            # Przygotuj kontekst (ostatnie 3 wiadomości)
            context = conversation_history[-3:] if conversation_history else []
            
            # LLM wybiera tools
            log_info(f"[COGNITIVE_ENGINE] 🔧 Analizuję intencję i wybieram tools...")
            selection = await analyze_intent_and_select_tools(message, context)
            
            needs_execution = selection.get("needs_execution", False)
            tools = selection.get("tools", [])
            reasoning = selection.get("reasoning", "")
            confidence = selection.get("confidence")
            
            log_info(f"[COGNITIVE_ENGINE] Tools selected: {needs_execution}, count: {len(tools)}")
            log_info(f"[COGNITIVE_ENGINE] Reasoning: {reasoning}")
            
            # Jeśli nie trzeba wykonywać tools, zwróć None
            if not needs_execution or not tools:
                if tools:
                    plan = self._format_tool_plan(tools)
                    return {
                        "tools_used": [],
                        "plan": plan,
                        "execution": [],
                        "summary": "Wykryto narzędzia, ale nie wymagają wykonania",
                        "reasoning": reasoning,
                        "confidence": confidence
                    }
                return None
            
            # Wykonaj wybrane tools
            log_info(f"[COGNITIVE_ENGINE] 🚀 Wykonuję {len(tools)} tools...")
            execution_results = await execute_selected_tools(tools, user_id)
            
            plan = self._format_tool_plan(tools)
            execution_details = self._merge_execution_with_plan(execution_results.get("results", []), plan)

            # Zwróć wyniki
            return {
                "tools_used": [t.get("tool") for t in execution_details if t.get("tool")],
                "plan": plan,
                "execution": execution_details,
                "summary": execution_results.get("summary", ""),
                "reasoning": reasoning,
                "confidence": confidence
            }
            
        except Exception as e:
            log_error(f"[COGNITIVE_ENGINE] Tool execution failed: {e}")
            return None
    
    def _create_empty_response(self) -> Dict[str, Any]:
        """Stwórz pustą odpowiedź"""
        return {
            "answer": "Nie otrzymałem żadnej wiadomości do przetworzenia.",
            "sources": [],
            "metadata": {"source": "empty_input"}
        }

    def _format_tool_plan(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Przygotuj plan narzędzi na podstawie specyfikacji"""

        plan = []
        for tool_spec in tools:
            name = tool_spec.get("name")
            tool_def = get_tool_by_name(name) if name else None

            endpoint = tool_def.get("endpoint") if tool_def else None
            method, path = None, None
            if endpoint and " " in endpoint:
                parts = endpoint.split(" ", 1)
                method = parts[0].strip()
                path = parts[1].strip()

            plan.append({
                "name": name,
                "description": tool_def.get("description") if tool_def else None,
                "endpoint": endpoint,
                "method": method,
                "path": path,
                "params": tool_spec.get("params", {}),
                "reason": tool_spec.get("reason"),
            })

        return plan

    def _merge_execution_with_plan(
        self,
        execution_results: List[Dict[str, Any]],
        plan: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Połącz wyniki wykonania z planem narzędzi"""

        plan_index = {item.get("name"): item for item in plan if item.get("name")}
        merged_results = []

        for result in execution_results:
            merged = dict(result)
            tool_name = result.get("tool")
            plan_entry = plan_index.get(tool_name)

            if plan_entry:
                merged.setdefault("method", plan_entry.get("method"))
                merged.setdefault("path", plan_entry.get("path"))
                merged.setdefault("description", plan_entry.get("description"))
                merged.setdefault("params", plan_entry.get("params"))
                merged.setdefault("endpoint", plan_entry.get("endpoint"))

            merged_results.append(merged)

        return merged_results
    
    def _create_error_response(self, error_msg: str) -> Dict[str, Any]:
        """Stwórz odpowiedź błędu"""
        return {
            "answer": f"Przepraszam, wystąpił błąd podczas przetwarzania: {error_msg}",
            "sources": [],
            "metadata": {
                "source": "error",
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    async def get_engine_status(self) -> Dict[str, Any]:
        """Pobierz status silnika kognitywnego"""
        
        try:
            # Status zaawansowanego silnika
            advanced_status = await self.advanced_engine.get_cognitive_status()
            
            return {
                "cognitive_engine": {
                    "version": "advanced_v2.0",
                    "performance_stats": self.performance_stats,
                    "systems_available": {
                        "advanced_cognitive_engine": True,
                        "hierarchical_memory": HIERARCHICAL_MEMORY_AVAILABLE,
                        "fast_path_handlers": FAST_PATH_AVAILABLE,
                        "web_research": WEB_RESEARCH_AVAILABLE,
                        "legacy_systems": LEGACY_SYSTEMS_AVAILABLE
                    }
                },
                "advanced_systems": advanced_status
            }
            
        except Exception as e:
            log_error(f"[COGNITIVE_ENGINE] Błąd pobierania statusu: {e}")
            return {
                "error": str(e),
                "cognitive_engine": {
                    "version": "advanced_v2.0",
                    "performance_stats": self.performance_stats
                }
            }

# Globalna instancja silnika
cognitive_engine = CognitiveEngine()
