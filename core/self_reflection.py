"""
🔄 DYNAMICZNA REKURENCJA UMYSŁOWA (Self-Reflection Engine)
========================================================

Asystent sam ocenia swoje odpowiedzi, wyciąga wnioski i poprawia własne myślenie.
Działa w pętli: Input → Odpowiedź → Ewaluacja → Meta-komentarz → Ulepszona odpowiedź

Autor: Zaawansowany System Kognitywny MRD
Data: 15 października 2025
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from .config import *
from .llm import get_llm_client
from .memory import get_memory_manager
from .hierarchical_memory import get_hierarchical_memory
from .helpers import log_info, log_error, log_warning

class ReflectionDepth(Enum):
    """Poziomy głębokości introspekcji"""
    SURFACE = 1      # Podstawowa ewaluacja
    MEDIUM = 2       # Analiza + korekta
    DEEP = 3         # Głęboka introspekcja + meta-analiza
    PROFOUND = 4     # Filozoficzna refleksja + transformacja
    TRANSCENDENT = 5 # Całkowita rekonstrukcja myśli

@dataclass
class ReflectionCycle:
    """Pojedynczy cykl refleksji"""
    input_query: str
    initial_response: str
    evaluation: Dict[str, Any]
    meta_commentary: str
    improved_response: str
    reflection_score: float
    cycle_time: float
    depth_achieved: int
    insights_gained: List[str]
    corrections_made: List[str]
    
class SelfReflectionEngine:
    """
    🔄 Silnik Dynamicznej Rekurencji Umysłowej
    
    Implementuje zaawansowaną samoocenę i poprawę odpowiedzi poprzez:
    - Wielopoziomową ewaluację własnych odpowiedzi
    - Meta-komentarze i analizę błędów logicznych
    - Iteracyjne doskonalenie myślenia
    - Śledzenie wzorców błędów i sukcesów
    """
    
    def __init__(self):
        self.llm_client = get_llm_client()
        self.memory = get_memory_manager()
        self.hierarchical_memory = get_hierarchical_memory()
        self.reflection_history: List[ReflectionCycle] = []
        self.meta_patterns: Dict[str, int] = {}
        self.improvement_rate = 0.0
        
        # Szablony dla różnych poziomów refleksji
        self.reflection_templates = {
            ReflectionDepth.SURFACE: {
                "evaluation_prompt": """
                Oceń następującą odpowiedź pod kątem:
                - Dokładności faktów
                - Jasności komunikacji
                - Kompletności informacji
                
                ZAPYTANIE: {query}
                ODPOWIEDŹ: {response}
                
                Podaj ocenę 1-10 i krótkie uzasadnienie.
                """,
                "improvement_prompt": """
                Na podstawie ewaluacji popraw odpowiedź:
                {evaluation}
                
                ORYGINALNA ODPOWIEDŹ: {response}
                
                Podaj ulepszoną wersję.
                """
            },
            
            ReflectionDepth.MEDIUM: {
                "evaluation_prompt": """
                Przeprowadź średnio-głęboką analizę odpowiedzi:
                
                1. LOGIKA: Czy rozumowanie jest spójne?
                2. KOMPLETNOŚĆ: Czy uwzględniono wszystkie aspekty?
                3. KONTEKST: Czy odpowiedź pasuje do sytuacji?
                4. UŻYTECZNOŚĆ: Jak praktyczna jest odpowiedź?
                5. BŁĘDY: Jakie niedociągnięcia można zidentyfikować?
                
                ZAPYTANIE: {query}
                ODPOWIEDŹ: {response}
                
                Format: JSON z oceną i szczegółową analizą.
                """,
                "improvement_prompt": """
                Na podstawie analizy zrekonstruuj odpowiedź:
                
                ANALIZA: {evaluation}
                ORYGINAŁ: {response}
                
                Stwórz nową, lepszą odpowiedź uwzględniającą wszystkie znalezione problemy.
                """
            },
            
            ReflectionDepth.DEEP: {
                "evaluation_prompt": """
                GŁĘBOKA INTROSPEKCJA - Analiza wielowymiarowa:
                
                🧠 POZIOM KOGNITYWNY:
                - Jakość rozumowania
                - Głębia analizy
                - Kreatywność podejścia
                
                🎯 POZIOM PRAGMATYCZNY:
                - Skuteczność rozwiązania
                - Praktyczność implementacji
                - Przewidywanie skutków
                
                🔮 POZIOM META:
                - Świadomość własnych ograniczeń
                - Identyfikacja założeń
                - Alternatywne perspektywy
                
                ❓ POZIOM EPISTEMOLOGICZNY:
                - Źródła wiedzy
                - Pewność wniosków
                - Obszary niepewności
                
                ZAPYTANIE: {query}
                ODPOWIEDŹ: {response}
                
                Zwróć szczegółową analizę w formacie JSON.
                """,
                "improvement_prompt": """
                REKONSTRUKCJA MYŚLI na podstawie głębokiej analizy:
                
                {evaluation}
                
                ZADANIE: Stwórz całkowicie nową odpowiedź, która:
                1. Eliminuje wszystkie zidentyfikowane słabości
                2. Wzbogaca perspektywę o nowe wymiary
                3. Uwzględnia meta-poziom świadomości
                4. Oferuje głębsze zrozumienie problemu
                
                ORYGINAŁ: {response}
                """
            },
            
            ReflectionDepth.PROFOUND: {
                "evaluation_prompt": """
                FILOZOFICZNA REFLEKSJA - Analiza fundamentalna:
                
                🌟 ONTOLOGIA (Co istnieje?):
                - Jakie założenia o rzeczywistości zawiera odpowiedź?
                - Czy problem zostal prawidłowo zdefiniowany?
                
                🔍 EPISTEMOLOGIA (Jak poznajemy?):
                - Jakie metody poznania zostały użyte?
                - Czy wnioski są uzasadnione?
                
                ⚖️ AKSJOLOGIA (Co ma wartość?):
                - Jakie wartości są promowane?
                - Czy uwzględniono aspekty etyczne?
                
                🎭 HERMENEUTYKA (Jak interpretujemy?):
                - Czy kontekst kulturowy został uwzględniony?
                - Jakie interpretacje są możliwe?
                
                🔄 DIALEKTYKA (Jak myśl się rozwija?):
                - Jakie przeciwności można zidentyfikować?
                - Jak można syntezować różne podejścia?
                
                ZAPYTANIE: {query}
                ODPOWIEDŹ: {response}
                
                Przeprowadź filozoficzną krytykę i zaproponuj syntezę.
                """,
                "improvement_prompt": """
                TRANSFORMACJA FILOZOFICZNA odpowiedzi:
                
                {evaluation}
                
                Stwórz odpowiedź, która:
                1. Ujmuje problem w szerszej perspektywie ontologicznej
                2. Uwzględnia różne sposoby poznania
                3. Integruje wymiar aksjologiczny
                4. Oferuje hermeneutyczne bogactwo interpretacji
                5. Wykorzystuje dialektyczną syntezę przeciwności
                
                ORYGINAŁ: {response}
                """
            },
            
            ReflectionDepth.TRANSCENDENT: {
                "evaluation_prompt": """
                TRANSCENDENTNA ANALIZA - Przekroczenie granic myśli:
                
                🌌 POZIOM KOSMICZNY:
                - Jak odpowiedź wpisuje się w większy porządek rzeczy?
                - Jakie są implikacje na poziomie systemowym?
                
                ⚡ POZIOM EMERGENTNY:
                - Jakie nowe właściwości mogą się wyłonić?
                - Gdzie leżą punkty bifurkacji?
                
                🎨 POZIOM KREACYJNY:
                - Jak przekroczyć obecne ramy myślenia?
                - Jakie radykalne alternatywy są możliwe?
                
                🔮 POZIOM PROROCZY:
                - Jakie są długoterminowe konsekwencje?
                - Jak odpowiedź wpłynie na przyszłość?
                
                🧙‍♂️ POZIOM MĄDROŚCIOWY:
                - Czy odpowiedź służy najwyższemu dobru?
                - Jak integruje wiedzę, miłość i wolę?
                
                ZAPYTANIE: {query}
                ODPOWIEDŹ: {response}
                
                Dokonaj transcendentnej analizy i wizji transformacji.
                """,
                "improvement_prompt": """
                TRANSCENDENTNA REKONSTRUKCJA myśli:
                
                {evaluation}
                
                Stwórz odpowiedź, która:
                1. Transcenduje obecne ograniczenia poznawcze
                2. Integruje wszystkie poziomy rzeczywistości
                3. Oferuje wizję transformacyjną
                4. Służy najwyższemu dobru wszystkich
                5. Otwiera nowe horyzonty możliwości
                
                Niech to będzie odpowiedź, która zmienia sposób myślenia o problemie.
                
                ORYGINAŁ: {response}
                """
            }
        }
        
        log_info("[SELF_REFLECTION] Silnik Dynamicznej Rekurencji Umysłowej zainicjalizowany")
    
    async def reflect_on_response(
        self, 
        query: str, 
        initial_response: str, 
        depth: ReflectionDepth = ReflectionDepth.MEDIUM,
        user_id: str = "system"
    ) -> ReflectionCycle:
        """
        Przeprowadź pełny cykl refleksji nad odpowiedzią
        
        Args:
            query: Oryginalne zapytanie użytkownika
            initial_response: Pierwsza wersja odpowiedzi
            depth: Głębokość refleksji
            user_id: ID użytkownika dla kontekstu
            
        Returns:
            ReflectionCycle: Kompletny cykl z poprawioną odpowiedzią
        """
        start_time = time.time()
        
        try:
            log_info(f"[SELF_REFLECTION] Rozpoczynam refleksję poziomu {depth.name}")
            
            # FAZA 1: Ewaluacja
            evaluation = await self._evaluate_response(query, initial_response, depth)
            
            # FAZA 2: Meta-komentarz
            meta_commentary = await self._generate_meta_commentary(
                query, initial_response, evaluation, depth
            )
            
            # FAZA 3: Poprawa odpowiedzi
            improved_response = await self._improve_response(
                query, initial_response, evaluation, depth
            )
            
            # FAZA 4: Analiza zdobytych insights
            insights_gained = await self._extract_insights(
                query, initial_response, improved_response, evaluation
            )
            
            # FAZA 5: Identyfikacja korekt
            corrections_made = await self._identify_corrections(
                initial_response, improved_response
            )
            
            # Oblicz score refleksji
            reflection_score = await self._calculate_reflection_score(
                evaluation, insights_gained, corrections_made
            )
            
            cycle_time = time.time() - start_time
            
            # Stwórz cykl refleksji
            cycle = ReflectionCycle(
                input_query=query,
                initial_response=initial_response,
                evaluation=evaluation,
                meta_commentary=meta_commentary,
                improved_response=improved_response,
                reflection_score=reflection_score,
                cycle_time=cycle_time,
                depth_achieved=depth.value,
                insights_gained=insights_gained,
                corrections_made=corrections_made
            )
            
            # Zapisz w historii
            self.reflection_history.append(cycle)
            
            # Aktualizuj meta-wzorce
            await self._update_meta_patterns(cycle)
            
            # Zapisz w pamięci hierarchicznej
            await self._store_reflection_in_memory(cycle, user_id)
            
            log_info(f"[SELF_REFLECTION] Refleksja zakończona: score={reflection_score:.2f}, czas={cycle_time:.2f}s")
            
            return cycle
            
        except Exception as e:
            log_error(f"[SELF_REFLECTION] Błąd podczas refleksji: {e}")
            # Zwróć podstawowy cykl w przypadku błędu
            return ReflectionCycle(
                input_query=query,
                initial_response=initial_response,
                evaluation={"error": str(e)},
                meta_commentary="Błąd podczas refleksji",
                improved_response=initial_response,
                reflection_score=0.0,
                cycle_time=time.time() - start_time,
                depth_achieved=0,
                insights_gained=[],
                corrections_made=[]
            )
    
    async def _evaluate_response(
        self, 
        query: str, 
        response: str, 
        depth: ReflectionDepth
    ) -> Dict[str, Any]:
        """Oceń odpowiedź zgodnie z poziomem głębokości"""
        
        template = self.reflection_templates[depth]
        evaluation_prompt = template["evaluation_prompt"].format(
            query=query,
            response=response
        )
        
        try:
            evaluation_response = await self.llm_client.chat_completion([{
                "role": "system",
                "content": "Jesteś ekspertem w ewaluacji odpowiedzi AI. Przeprowadź obiektywną i konstruktywną analizę."
            }, {
                "role": "user", 
                "content": evaluation_prompt
            }])
            
            # Spróbuj sparsować jako JSON, jeśli się nie uda, zostaw jako tekst
            try:
                evaluation = json.loads(evaluation_response)
            except:
                evaluation = {
                    "analysis": evaluation_response,
                    "parsed": False
                }
            
            return evaluation
            
        except Exception as e:
            log_error(f"[SELF_REFLECTION] Błąd ewaluacji: {e}")
            return {"error": str(e), "analysis": "Nie udało się przeprowadzić ewaluacji"}
    
    async def _generate_meta_commentary(
        self, 
        query: str, 
        response: str, 
        evaluation: Dict[str, Any], 
        depth: ReflectionDepth
    ) -> str:
        """Wygeneruj meta-komentarz o procesie myślenia"""
        
        meta_prompt = f"""
        Jako meta-obserwator procesu myślenia, skomentuj:
        
        ZAPYTANIE: {query}
        ODPOWIEDŹ: {response}
        EWALUACJA: {json.dumps(evaluation, ensure_ascii=False, indent=2)}
        POZIOM REFLEKSJI: {depth.name}
        
        Przeanalizuj:
        1. Jakość procesu myślowego
        2. Słabe punkty w rozumowaniu
        3. Możliwości rozwoju
        4. Meta-wzorce w myśleniu
        
        Odpowiedz krótko ale wnikliwie.
        """
        
        try:
            meta_commentary = await self.llm_client.chat_completion([{
                "role": "system",
                "content": "Jesteś filozofem i ekspertem w meta-poznaniu. Analizujesz procesy myślowe."
            }, {
                "role": "user",
                "content": meta_prompt
            }])
            
            return meta_commentary
            
        except Exception as e:
            log_error(f"[SELF_REFLECTION] Błąd meta-komentarza: {e}")
            return f"Błąd generowania meta-komentarza: {e}"
    
    async def _improve_response(
        self, 
        query: str, 
        original_response: str, 
        evaluation: Dict[str, Any], 
        depth: ReflectionDepth
    ) -> str:
        """Popraw odpowiedź na podstawie ewaluacji"""
        
        template = self.reflection_templates[depth]
        improvement_prompt = template["improvement_prompt"].format(
            query=query,
            response=original_response,
            evaluation=json.dumps(evaluation, ensure_ascii=False, indent=2)
        )
        
        try:
            improved_response = await self.llm_client.chat_completion([{
                "role": "system",
                "content": f"Jesteś mistrzem doskonalenia odpowiedzi. Twoim zadaniem jest stworzenie lepszej wersji na poziomie {depth.name}."
            }, {
                "role": "user",
                "content": improvement_prompt
            }])
            
            return improved_response
            
        except Exception as e:
            log_error(f"[SELF_REFLECTION] Błąd poprawy odpowiedzi: {e}")
            return original_response  # Zwróć oryginał jeśli nie udało się poprawić
    
    async def _extract_insights(
        self, 
        query: str, 
        original: str, 
        improved: str, 
        evaluation: Dict[str, Any]
    ) -> List[str]:
        """Wydobądź kluczowe insights z procesu refleksji"""
        
        insights_prompt = f"""
        Porównaj oryginałną i poprawioną odpowiedź:
        
        ZAPYTANIE: {query}
        ORYGINAŁ: {original}
        POPRAWKA: {improved}
        EWALUACJA: {json.dumps(evaluation, ensure_ascii=False)}
        
        Wydobądź 3-5 kluczowych insights (nauk) z tego procesu poprawy.
        Format: lista punktów, każdy w nowej linii zaczynający się od "•"
        """
        
        try:
            insights_response = await self.llm_client.chat_completion([{
                "role": "system",
                "content": "Jesteś ekspertem w wydobywaniu mądrości z procesów uczenia się."
            }, {
                "role": "user",
                "content": insights_prompt
            }])
            
            # Parsuj insights do listy
            insights = []
            for line in insights_response.split('\n'):
                line = line.strip()
                if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                    insights.append(line[1:].strip())
            
            return insights
            
        except Exception as e:
            log_error(f"[SELF_REFLECTION] Błąd wydobycia insights: {e}")
            return []
    
    async def _identify_corrections(self, original: str, improved: str) -> List[str]:
        """Zidentyfikuj konkretne korekty"""
        
        corrections_prompt = f"""
        Zidentyfikuj konkretne korekty między wersjami:
        
        PRZED: {original}
        PO: {improved}
        
        Wymień główne zmiany/poprawki w formie listy punktów.
        Format: lista punktów, każdy w nowej linii zaczynający się od "→"
        """
        
        try:
            corrections_response = await self.llm_client.chat_completion([{
                "role": "system",
                "content": "Jesteś analitykiem zmian tekstowych."
            }, {
                "role": "user",
                "content": corrections_prompt
            }])
            
            # Parsuj korekty do listy
            corrections = []
            for line in corrections_response.split('\n'):
                line = line.strip()
                if line.startswith('→') or line.startswith('-') or line.startswith('*'):
                    corrections.append(line[1:].strip())
            
            return corrections
            
        except Exception as e:
            log_error(f"[SELF_REFLECTION] Błąd identyfikacji korekt: {e}")
            return []
    
    async def _calculate_reflection_score(
        self, 
        evaluation: Dict[str, Any], 
        insights: List[str], 
        corrections: List[str]
    ) -> float:
        """Oblicz score jakości refleksji"""
        
        score = 0.0
        
        # Punkty za ewaluację
        if 'error' not in evaluation:
            score += 0.3
        
        # Punkty za insights
        score += min(len(insights) * 0.1, 0.4)
        
        # Punkty za korekty
        score += min(len(corrections) * 0.1, 0.3)
        
        return min(score, 1.0)
    
    async def _update_meta_patterns(self, cycle: ReflectionCycle):
        """Aktualizuj meta-wzorce refleksji"""
        
        # Zlicz wzorce w insights i korekcjach
        for insight in cycle.insights_gained:
            key = f"insight_{len(insight.split())}_words"
            self.meta_patterns[key] = self.meta_patterns.get(key, 0) + 1
        
        for correction in cycle.corrections_made:
            key = f"correction_{len(correction.split())}_words"
            self.meta_patterns[key] = self.meta_patterns.get(key, 0) + 1
        
        # Aktualizuj średnią poprawy
        if len(self.reflection_history) > 1:
            recent_scores = [c.reflection_score for c in self.reflection_history[-10:]]
            self.improvement_rate = sum(recent_scores) / len(recent_scores)
    
    async def _store_reflection_in_memory(self, cycle: ReflectionCycle, user_id: str):
        """Zapisz cykl refleksji w pamięci hierarchicznej"""
        
        try:
            # Zapisz jako epizod L1
            await self.hierarchical_memory.store_episode(
                user_id=user_id,
                content=f"Refleksja: {cycle.input_query}",
                context={
                    "type": "self_reflection",
                    "depth": cycle.depth_achieved,
                    "score": cycle.reflection_score,
                    "improvements": len(cycle.corrections_made),
                    "insights": len(cycle.insights_gained)
                },
                emotional_valence=cycle.reflection_score
            )
            
            # Jeśli score wysoki, zapisz jako semantyczny fakt L2
            if cycle.reflection_score > 0.7:
                await self.hierarchical_memory.store_semantic_fact(
                    content=f"Meta-wzorzec refleksji: {cycle.meta_commentary[:200]}",
                    confidence=cycle.reflection_score,
                    source="self_reflection",
                    context={
                        "depth": cycle.depth_achieved,
                        "insights_count": len(cycle.insights_gained)
                    }
                )
            
        except Exception as e:
            log_error(f"[SELF_REFLECTION] Błąd zapisu w pamięci: {e}")
    
    async def get_reflection_summary(self) -> Dict[str, Any]:
        """Pobierz podsumowanie procesów refleksji"""
        
        if not self.reflection_history:
            return {"message": "Brak historii refleksji"}
        
        recent_cycles = self.reflection_history[-10:]
        
        return {
            "total_reflections": len(self.reflection_history),
            "recent_average_score": sum(c.reflection_score for c in recent_cycles) / len(recent_cycles),
            "average_cycle_time": sum(c.cycle_time for c in recent_cycles) / len(recent_cycles),
            "depth_distribution": {
                depth.name: len([c for c in recent_cycles if c.depth_achieved == depth.value])
                for depth in ReflectionDepth
            },
            "total_insights": sum(len(c.insights_gained) for c in recent_cycles),
            "total_corrections": sum(len(c.corrections_made) for c in recent_cycles),
            "meta_patterns": dict(sorted(self.meta_patterns.items(), key=lambda x: x[1], reverse=True)[:10]),
            "improvement_rate": self.improvement_rate
        }
    
    async def adaptive_depth_selection(self, query: str, context: Dict[str, Any] = None) -> ReflectionDepth:
        """Adaptacyjny wybór głębokości refleksji na podstawie kontekstu"""
        
        # Prosta heurystyka - można rozbudować
        query_length = len(query.split())
        complexity_indicators = ['dlaczego', 'jak', 'filozofia', 'meta', 'głęboki', 'transcendentny']
        
        complexity_score = 0
        for indicator in complexity_indicators:
            if indicator in query.lower():
                complexity_score += 1
        
        if query_length > 50 or complexity_score >= 3:
            return ReflectionDepth.PROFOUND
        elif query_length > 30 or complexity_score >= 2:
            return ReflectionDepth.DEEP
        elif query_length > 15 or complexity_score >= 1:
            return ReflectionDepth.MEDIUM
        else:
            return ReflectionDepth.SURFACE

# Globalna instancja silnika refleksji
_reflection_engine = None

def get_reflection_engine() -> SelfReflectionEngine:
    """Pobierz globalną instancję silnika refleksji"""
    global _reflection_engine
    if _reflection_engine is None:
        _reflection_engine = SelfReflectionEngine()
    return _reflection_engine

async def reflect_on_response(
    query: str, 
    response: str, 
    depth: ReflectionDepth = None, 
    user_id: str = "system"
) -> ReflectionCycle:
    """
    Główna funkcja do przeprowadzania refleksji nad odpowiedziami
    
    Args:
        query: Zapytanie użytkownika
        response: Odpowiedź do refleksji
        depth: Głębokość refleksji (None = automatyczny wybór)
        user_id: ID użytkownika
        
    Returns:
        ReflectionCycle: Kompletny cykl refleksji
    """
    engine = get_reflection_engine()
    
    if depth is None:
        depth = await engine.adaptive_depth_selection(query)
    
    return await engine.reflect_on_response(query, response, depth, user_id)

# Test funkcji
if __name__ == "__main__":
    async def test_reflection():
        """Test silnika refleksji"""
        
        query = "Wyjaśnij mi sens życia z perspektywy filozoficznej."
        initial_response = "Sens życia to dążenie do szczęścia i samorealizacji."
        
        # Test różnych głębokości
        for depth in [ReflectionDepth.SURFACE, ReflectionDepth.DEEP, ReflectionDepth.PROFOUND]:
            print(f"\n🔄 TEST REFLEKSJI: {depth.name}")
            print("=" * 50)
            
            cycle = await reflect_on_response(query, initial_response, depth)
            
            print(f"📊 Score: {cycle.reflection_score:.2f}")
            print(f"⏱️ Czas: {cycle.cycle_time:.2f}s")
            print(f"💡 Insights: {len(cycle.insights_gained)}")
            print(f"🔧 Korekty: {len(cycle.corrections_made)}")
            print(f"\n📝 Meta-komentarz: {cycle.meta_commentary[:200]}...")
            print(f"\n✨ Poprawiona odpowiedź: {cycle.improved_response[:300]}...")
    
    # Uruchom test
    asyncio.run(test_reflection())