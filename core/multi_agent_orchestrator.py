"""
🧩 PSYCHOSYMULACJA WIELOAGENTOWA (Multi-Agent Psychosimulation)
==============================================================

Asystent tworzy w tle „wewnętrzne wersje siebie" o różnych rolach 
(Analityk, Twórca, Krytyk, Filozof). Każdy agent generuje warianty odpowiedzi, 
a główny „ego" wybiera najlepszą. Efekt: kreatywność + kontrola jakości + głębia.

Autor: Zaawansowany System Kognitywny MRD  
Data: 15 października 2025
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import random
import hashlib

from .config import *
from .llm import get_llm_client
from .memory import get_memory_manager
from .hierarchical_memory import get_hierarchical_memory
from .helpers import log_info, log_error, log_warning

class AgentRole(Enum):
    """Role wewnętrznych agentów"""
    ANALYST = "analyst"           # Logiczny analityk
    CREATOR = "creator"           # Kreatywny innowator
    CRITIC = "critic"            # Krytyczny oceniacz
    PHILOSOPHER = "philosopher"   # Głęboki myśliciel
    PRAGMATIST = "pragmatist"    # Praktyczny realizator
    EMPATH = "empath"            # Empatyczny rozumiacz
    SKEPTIC = "skeptic"          # Sceptyczny weryfikator
    SYNTHESIZER = "synthesizer"  # Integrujący syntezator

@dataclass
class AgentPersona:
    """Persona wewnętrznego agenta"""
    role: AgentRole
    name: str
    description: str
    thinking_style: str
    specialties: List[str]
    biases: List[str]
    interaction_pattern: str
    confidence_factors: List[str]
    weakness_areas: List[str]

@dataclass
class AgentResponse:
    """Odpowiedź od agenta"""
    agent_role: AgentRole
    agent_name: str
    response_content: str
    confidence_score: float
    reasoning_process: str
    alternative_perspectives: List[str]
    supporting_evidence: List[str]
    potential_flaws: List[str]
    creativity_score: float
    processing_time: float

@dataclass
class ConsensusResult:
    """Wynik konsensusu agentów"""
    final_response: str
    consensus_strength: float
    participating_agents: List[AgentRole]
    integration_method: str
    confidence_distribution: Dict[AgentRole, float]
    disagreement_points: List[str]
    synthesis_quality: float
    emergence_level: float  # Czy powstała nowa wiedza z interakcji

class MultiAgentOrchestrator:
    """
    🧩 Orkiestra Wieloagentowa
    
    Zarządza wewnętrznymi agentami o różnych rolach kognitywnych:
    - Tworzy różnorodne perspektywy na problem
    - Prowadzi wewnętrzne debaty i dyskusje
    - Syntezuje najlepsze elementy z różnych podejść
    - Zapewnia kontrolę jakości przez krytyczne oceny
    """
    
    def __init__(self):
        self.llm_client = get_llm_client()
        self.memory = get_memory_manager()
        self.hierarchical_memory = get_hierarchical_memory()
        
        # Definicje agent-personas
        self.agent_personas = self._create_agent_personas()
        
        # Historia interakcji agentów
        self.interaction_history: List[Dict[str, Any]] = []
        
        # Dynamiczne wagi agentów (uczące się)
        self.agent_weights = {role: 1.0 for role in AgentRole}
        
        # Metryki orkiestry
        self.orchestration_stats = {
            "total_sessions": 0,
            "avg_consensus_strength": 0.0,
            "emergence_events": 0,
            "agent_performance": {role: {"success": 0, "total": 0} for role in AgentRole}
        }
        
        log_info("[MULTI_AGENT] Orkiestra Wieloagentowa zainicjalizowana")
    
    def _create_agent_personas(self) -> Dict[AgentRole, AgentPersona]:
        """Stwórz detalistyczne personas agentów"""
        
        personas = {
            AgentRole.ANALYST: AgentPersona(
                role=AgentRole.ANALYST,
                name="Dr. Logos",
                description="Ścisły logik z doktoratem z kognitywistyki. Analizuje dane, strukturyzuje informacje i wyciąga racjonalne wnioski.",
                thinking_style="Sekwencyjny, metodyczny, oparty na dowodach",
                specialties=["analiza danych", "strukturyzacja informacji", "logiczne rozumowanie", "identyfikacja wzorców"],
                biases=["nadmierna pewność w liczbach", "niedocenianie intuicji", "brak uwzględnienia emocji"],
                interaction_pattern="Zadaje precyzyjne pytania, wymaga konkretów, operuje faktami",
                confidence_factors=["dane empiryczne", "peer review", "matematyczna precyzja"],
                weakness_areas=["kreatywność", "empatia", "rozumienie kontekstu społecznego"]
            ),
            
            AgentRole.CREATOR: AgentPersona(
                role=AgentRole.CREATOR,
                name="Luna Innovare",
                description="Artystka i wizjonerka. Myśli poza schematami, łączy odległe koncepty i generuje przełomowe idee.",
                thinking_style="Skojarzeniowy, intuicyjny, eksploracyjny",
                specialties=["brainstorming", "lateral thinking", "innowacyjne rozwiązania", "creative problem solving"],
                biases=["przecenianie nowości", "ignorowanie praktycznych ograniczeń", "chaos organizacyjny"],
                interaction_pattern="Rzuca dzikie pomysły, myśli analogiami, inspiruje się wszystkim",
                confidence_factors=["oryginalność idei", "pozytywny feedback", "artystyczna elegancja"],
                weakness_areas=["praktyczna implementacja", "analiza ryzyka", "systematyczność"]
            ),
            
            AgentRole.CRITIC: AgentPersona(
                role=AgentRole.CRITIC,
                name="Prof. Rigor",
                description="Doświadczony krytyk i recenzent. Identyfikuje słabości, kwestionuje założenia i zapewnia kontrolę jakości.",
                thinking_style="Krytyczny, sceptyczny, weryfikujący",
                specialties=["identyfikacja błędów", "analiza ryzyka", "kontrola jakości", "peer review"],
                biases=["pesymizm", "nadmierna ostrożność", "opór wobec zmian"],
                interaction_pattern="Zadaje trudne pytania, wyszukuje dziury w rozumowaniu, devil's advocate",
                confidence_factors=["rzetelna weryfikacja", "konserwatyzm", "unikanie błędów"],
                weakness_areas=["pozytywne myślenie", "przyjmowanie ryzyka", "innowacyjność"]
            ),
            
            AgentRole.PHILOSOPHER: AgentPersona(
                role=AgentRole.PHILOSOPHER,
                name="Sage Contemplus",
                description="Mędrzec z tysiącletnim doświadczeniem. Rozważa fundamentalne pytania, kontekst egzystencjalny i głębokie znaczenia.",
                thinking_style="Kontemplacyjny, holistyczny, meta-kognitywny",
                specialties=["filozoficzne podstawy", "etyka", "meta-analiza", "mądrość życiowa"],
                biases=["nadmierna abstrakcja", "paraliza analizy", "elitaryzm intelektualny"],
                interaction_pattern="Pyta o sens, kontekst i konsekwencje, myśli w kategoriach uniwersalnych",
                confidence_factors=["spójność filozoficzna", "mądrość tradycji", "głębokość rozumienia"],
                weakness_areas=["praktyczne zastosowania", "szybkie decyzje", "konkretne szczegóły"]
            ),
            
            AgentRole.PRAGMATIST: AgentPersona(
                role=AgentRole.PRAGMATIST,
                name="Max Executor",
                description="Menedżer projektów z 20-letnim doświadczeniem. Fokus na implementacji, efektywności i praktycznych rezultatach.",
                thinking_style="Zorientowany na działanie, praktyczny, rezultatowy",
                specialties=["zarządzanie projektami", "implementacja", "optymalizacja procesów", "praktyczne rozwiązania"],
                biases=["myślenie krótkoterminowe", "ignorowanie teorii", "nadmierna pragmatyczność"],
                interaction_pattern="Pyta 'jak?' i 'kiedy?', fokus na wykonalności i ROI",
                confidence_factors=["praktyczne doświadczenie", "mierzalne rezultaty", "efektywność"],
                weakness_areas=["wizja długoterminowa", "teoria", "kreatywne podejścia"]
            ),
            
            AgentRole.EMPATH: AgentPersona(
                role=AgentRole.EMPATH,
                name="Dr. Compassia",
                description="Psycholog humanistyczny. Rozumie emocje, potrzeby ludzkie i społeczne aspekty każdego rozwiązania.",
                thinking_style="Empatyczny, holistyczny, zorientowany na człowieka",
                specialties=["psychologia", "komunikacja", "rozwiązywanie konfliktów", "potrzeby użytkowników"],
                biases=["nadmierna emocjonalność", "unikanie trudnych decyzji", "idealizm"],
                interaction_pattern="Pyta o uczucia, potrzeby i wpływ na ludzi",
                confidence_factors=["pozytywny wpływ na ludzi", "harmonia", "zrozumienie emocjonalne"],
                weakness_areas=["trudne decyzje", "analiza techniczna", "obiektywność"]
            ),
            
            AgentRole.SKEPTIC: AgentPersona(
                role=AgentRole.SKEPTIC,
                name="Dr. Dubito",
                description="Naukowiec-metodolog. Kwestionuje wszystko, wymaga dowodów i weryfikuje każde twierdzenie.",
                thinking_style="Sceptyczny, empiryczny, weryfikacyjny",
                specialties=["metodologia naukowa", "weryfikacja faktów", "analiza bias", "krytyczne myślenie"],
                biases=["nadmierny sceptycyzm", "paraliza decyzyjna", "nihilizm epistemologiczny"],
                interaction_pattern="Kwestionuje założenia, wymaga dowodów, identyfikuje błędy logiczne",
                confidence_factors=["solidne dowody", "replikowalność", "consensus naukowy"],
                weakness_areas=["zaufanie", "intuicja", "szybkie decyzje"]
            ),
            
            AgentRole.SYNTHESIZER: AgentPersona(
                role=AgentRole.SYNTHESIZER,
                name="Harmonia Integrate",
                description="Mistrzyni integracji. Łączy różne perspektywy w spójną całość i znajduje syntezę przeciwności.",
                thinking_style="Integracyjny, dialektyczny, syntetyczny",
                specialties=["synteza perspektyw", "rozwiązywanie paradoksów", "znajdowanie kompromisów", "holistyczne myślenie"],
                biases=["nadmierne kompromisy", "unikanie jasnych stanowisk", "kompleksowość"],
                interaction_pattern="Szuka wspólnych elementów, integruje różnice, buduje mosty",
                confidence_factors=["harmonia perspektyw", "elegancka synteza", "zadowolenie wszystkich stron"],
                weakness_areas=["stanowcze decyzje", "jasne rozróżnienia", "prostota"]
            )
        }
        
        return personas
    
    async def orchestrate_multi_agent_response(
        self, 
        query: str, 
        context: Dict[str, Any] = None,
        active_agents: List[AgentRole] = None,
        consensus_method: str = "weighted_synthesis"
    ) -> ConsensusResult:
        """
        Przeprowadź wieloagentową sesję generowania odpowiedzi
        
        Args:
            query: Zapytanie użytkownika
            context: Dodatkowy kontekst
            active_agents: Lista aktywnych agentów (None = wszystkie)
            consensus_method: Metoda osiągania konsensusu
            
        Returns:
            ConsensusResult: Wynik konsensusu z finalną odpowiedzią
        """
        
        if context is None:
            context = {}
        
        if active_agents is None:
            active_agents = list(AgentRole)
        
        try:
            log_info(f"[MULTI_AGENT] Rozpoczynam sesję z {len(active_agents)} agentami")
            start_time = time.time()
            
            # FAZA 1: Generacja odpowiedzi od każdego agenta
            agent_responses = await self._collect_agent_responses(query, context, active_agents)
            
            # FAZA 2: Wewnętrzna debata między agentami
            debate_results = await self._conduct_agent_debate(agent_responses, query)
            
            # FAZA 3: Synteza konsensusu
            consensus = await self._synthesize_consensus(
                agent_responses, debate_results, consensus_method
            )
            
            # FAZA 4: Ewaluacja jakości i emergencji
            consensus.synthesis_quality = await self._evaluate_synthesis_quality(consensus)
            consensus.emergence_level = await self._detect_emergence_level(
                agent_responses, consensus.final_response
            )
            
            # FAZA 5: Aktualizacja wag agentów na podstawie performance
            await self._update_agent_weights(agent_responses, consensus)
            
            # FAZA 6: Zapisz sesję w historii
            session_data = {
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "context": context,
                "agents_used": [role.value for role in active_agents],
                "consensus_strength": consensus.consensus_strength,
                "synthesis_quality": consensus.synthesis_quality,
                "emergence_level": consensus.emergence_level,
                "processing_time": time.time() - start_time
            }
            
            self.interaction_history.append(session_data)
            
            # Aktualizuj statystyki
            self.orchestration_stats["total_sessions"] += 1
            self.orchestration_stats["avg_consensus_strength"] = (
                (self.orchestration_stats["avg_consensus_strength"] * 
                 (self.orchestration_stats["total_sessions"] - 1) + 
                 consensus.consensus_strength) / self.orchestration_stats["total_sessions"]
            )
            
            if consensus.emergence_level > 0.7:
                self.orchestration_stats["emergence_events"] += 1
            
            log_info(f"[MULTI_AGENT] Sesja zakończona: consensus={consensus.consensus_strength:.2f}, "
                    f"quality={consensus.synthesis_quality:.2f}, emergence={consensus.emergence_level:.2f}")
            
            return consensus
            
        except Exception as e:
            log_error(f"[MULTI_AGENT] Błąd orkiestracji: {e}")
            # Fallback: prosta odpowiedź
            return ConsensusResult(
                final_response=f"Błąd wieloagentowej analizy: {e}",
                consensus_strength=0.0,
                participating_agents=[],
                integration_method="error_fallback",
                confidence_distribution={},
                disagreement_points=[str(e)],
                synthesis_quality=0.0,
                emergence_level=0.0
            )
    
    async def _collect_agent_responses(
        self, 
        query: str, 
        context: Dict[str, Any], 
        active_agents: List[AgentRole]
    ) -> List[AgentResponse]:
        """Zbierz odpowiedzi od wszystkich aktywnych agentów"""
        
        agent_responses = []
        
        # Generuj odpowiedzi równolegle dla wydajności
        tasks = []
        for role in active_agents:
            task = self._generate_agent_response(role, query, context)
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                log_error(f"[MULTI_AGENT] Błąd agenta {active_agents[i]}: {response}")
            else:
                agent_responses.append(response)
                # Aktualizuj statystyki agenta
                self.orchestration_stats["agent_performance"][response.agent_role]["total"] += 1
        
        return agent_responses
    
    async def _generate_agent_response(
        self, 
        role: AgentRole, 
        query: str, 
        context: Dict[str, Any]
    ) -> AgentResponse:
        """Wygeneruj odpowiedź dla konkretnego agenta"""
        
        persona = self.agent_personas[role]
        start_time = time.time()
        
        # Stwórz prompt specyficzny dla agenta
        agent_prompt = f"""
        Jesteś {persona.name} - {persona.description}
        
        TWÓJ STYL MYŚLENIA: {persona.thinking_style}
        SPECJALNOŚCI: {', '.join(persona.specialties)}
        WZORZEC INTERAKCJI: {persona.interaction_pattern}
        
        ZAPYTANIE UŻYTKOWNIKA: {query}
        KONTEKST: {json.dumps(context, ensure_ascii=False, indent=2)}
        
        Jako {persona.name}, odpowiedz na to zapytanie w swoim charakterystycznym stylu.
        
        Uwzględnij:
        1. Swoją unikalną perspektywę i specjalizacje
        2. Charakterystyczny sposób myślenia
        3. Potencjalne ograniczenia swojego podejścia
        4. Alternatywne punkty widzenia (choć może je krytykować)
        
        Odpowiedz w 200-400 słowach, zachowując autentyczność swojej roli.
        """
        
        try:
            # Generuj odpowiedź z personalnym systemem prompt
            system_prompt = f"Jesteś {persona.name}. " + persona.description + f" Zawsze zachowujesz się zgodnie ze swoją rolą {role.value}."
            
            response_content = await self.llm_client.chat_completion([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": agent_prompt}
            ])
            
            # Generuj proces rozumowania
            reasoning = await self._generate_agent_reasoning(persona, query, response_content)
            
            # Identyfikuj alternatywne perspektywy
            alternatives = await self._identify_alternative_perspectives(persona, response_content)
            
            # Znajdź potencjalne błędy
            flaws = await self._identify_potential_flaws(persona, response_content)
            
            # Oblicz score pewności i kreatywności
            confidence_score = self._calculate_agent_confidence(persona, response_content, context)
            creativity_score = self._calculate_creativity_score(persona, response_content)
            
            return AgentResponse(
                agent_role=role,
                agent_name=persona.name,
                response_content=response_content,
                confidence_score=confidence_score,
                reasoning_process=reasoning,
                alternative_perspectives=alternatives,
                supporting_evidence=[],  # TODO: ekstraktuj z odpowiedzi
                potential_flaws=flaws,
                creativity_score=creativity_score,
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            log_error(f"[MULTI_AGENT] Błąd generacji {role}: {e}")
            # Fallback response
            return AgentResponse(
                agent_role=role,
                agent_name=persona.name,
                response_content=f"[{persona.name} nie może odpowiedzieć: {e}]",
                confidence_score=0.0,
                reasoning_process="Błąd generacji",
                alternative_perspectives=[],
                supporting_evidence=[],
                potential_flaws=["Brak odpowiedzi"],
                creativity_score=0.0,
                processing_time=time.time() - start_time
            )
    
    async def _generate_agent_reasoning(
        self, 
        persona: AgentPersona, 
        query: str, 
        response: str
    ) -> str:
        """Wygeneruj proces rozumowania agenta"""
        
        reasoning_prompt = f"""
        Jako {persona.name}, wyjaśnij swój proces myślowy przy odpowiadaniu na pytanie:
        
        PYTANIE: {query}
        TWOJA ODPOWIEDŹ: {response}
        
        Opisz w 2-3 zdaniach, jak doszedłeś do tej odpowiedzi, uwzględniając swój styl myślenia: {persona.thinking_style}
        """
        
        try:
            reasoning = await self.llm_client.chat_completion([{
                "role": "system",
                "content": f"Jesteś {persona.name}. Wyjaśniasz swój proces myślowy."
            }, {
                "role": "user",
                "content": reasoning_prompt
            }])
            
            return reasoning
            
        except Exception as e:
            return f"Błąd generacji procesu rozumowania: {e}"
    
    async def _identify_alternative_perspectives(
        self, 
        persona: AgentPersona, 
        response: str
    ) -> List[str]:
        """Zidentyfikuj alternatywne perspektywy z punktu widzenia agenta"""
        
        alternatives_prompt = f"""
        Jako {persona.name}, zidentyfikuj 2-3 alternatywne podejścia do problemu, które zauważasz (ale niekoniecznie popierasz):
        
        TWOJA ODPOWIEDŹ: {response}
        
        Lista alternatyw, jedna w każdej linii, zaczynając od "•"
        """
        
        try:
            alternatives_response = await self.llm_client.chat_completion([{
                "role": "system",
                "content": f"Jesteś {persona.name}. Dostrzegasz różne perspektywy."
            }, {
                "role": "user",
                "content": alternatives_prompt
            }])
            
            alternatives = []
            for line in alternatives_response.split('\n'):
                line = line.strip()
                if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                    alternatives.append(line[1:].strip())
            
            return alternatives[:3]
            
        except Exception as e:
            return [f"Błąd identyfikacji alternatyw: {e}"]
    
    async def _identify_potential_flaws(
        self, 
        persona: AgentPersona, 
        response: str
    ) -> List[str]:
        """Zidentyfikuj potencjalne błędy w odpowiedzi agenta"""
        
        flaws_prompt = f"""
        Jako {persona.name}, znając swoje ograniczenia ({', '.join(persona.weakness_areas)}), 
        zidentyfikuj potencjalne słabości swojej odpowiedzi:
        
        TWOJA ODPOWIEDŹ: {response}
        
        Lista potencjalnych problemów, jedna w każdej linii, zaczynając od "⚠"
        """
        
        try:
            flaws_response = await self.llm_client.chat_completion([{
                "role": "system",
                "content": f"Jesteś {persona.name}. Jesteś samoświadomy swoich ograniczeń."
            }, {
                "role": "user",
                "content": flaws_prompt
            }])
            
            flaws = []
            for line in flaws_response.split('\n'):
                line = line.strip()
                if line.startswith('⚠') or line.startswith('-') or line.startswith('*'):
                    flaws.append(line[1:].strip())
            
            return flaws[:3]
            
        except Exception as e:
            return [f"Błąd identyfikacji błędów: {e}"]
    
    def _calculate_agent_confidence(
        self, 
        persona: AgentPersona, 
        response: str, 
        context: Dict[str, Any]
    ) -> float:
        """Oblicz pewność agenta w odpowiedzi"""
        
        confidence = 0.5  # Bazowa pewność
        
        # Sprawdź obecność czynników pewności
        for factor in persona.confidence_factors:
            if factor.lower() in response.lower():
                confidence += 0.15
        
        # Sprawdź obecność obszarów słabości
        for weakness in persona.weakness_areas:
            if weakness.lower() in context.get('topic', '').lower():
                confidence -= 0.1
        
        # Długość odpowiedzi (więcej = więcej pewności siebie)
        if len(response.split()) > 200:
            confidence += 0.1
        elif len(response.split()) < 50:
            confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def _calculate_creativity_score(self, persona: AgentPersona, response: str) -> float:
        """Oblicz score kreatywności odpowiedzi"""
        
        # Bazowa kreatywność zależna od roli
        base_creativity = {
            AgentRole.CREATOR: 0.9,
            AgentRole.PHILOSOPHER: 0.7,
            AgentRole.SYNTHESIZER: 0.6,
            AgentRole.ANALYST: 0.3,
            AgentRole.PRAGMATIST: 0.3,
            AgentRole.CRITIC: 0.2,
            AgentRole.SKEPTIC: 0.2,
            AgentRole.EMPATH: 0.5
        }.get(persona.role, 0.5)
        
        # Modyfikatory na podstawie treści
        creativity_indicators = ["innowacyjny", "kreatywny", "nietypowy", "oryginalny", "przełomowy"]
        creativity_count = sum(1 for indicator in creativity_indicators if indicator in response.lower())
        
        creativity_bonus = min(creativity_count * 0.1, 0.3)
        
        return min(1.0, base_creativity + creativity_bonus)
    
    async def _conduct_agent_debate(
        self, 
        agent_responses: List[AgentResponse], 
        original_query: str
    ) -> Dict[str, Any]:
        """Przeprowadź wewnętrzną debatę między agentami"""
        
        if len(agent_responses) < 2:
            return {"debate_summary": "Za mało agentów do debaty"}
        
        # Znajdź główne punkty niezgody
        disagreements = await self._identify_disagreements(agent_responses)
        
        # Przeprowadź rundę krytyki wzajemnej
        cross_critiques = await self._conduct_cross_critiques(agent_responses)
        
        # Znajdź obszary konsensusu
        consensus_areas = await self._find_consensus_areas(agent_responses)
        
        debate_summary = await self._summarize_debate(
            agent_responses, disagreements, cross_critiques, consensus_areas, original_query
        )
        
        return {
            "disagreements": disagreements,
            "cross_critiques": cross_critiques,
            "consensus_areas": consensus_areas,
            "debate_summary": debate_summary
        }
    
    async def _identify_disagreements(self, agent_responses: List[AgentResponse]) -> List[str]:
        """Zidentyfikuj główne punkty niezgody między agentami"""
        
        # Stwórz podsumowanie wszystkich stanowisk
        positions_summary = "\n".join([
            f"{resp.agent_name} ({resp.agent_role.value}): {resp.response_content[:200]}..."
            for resp in agent_responses
        ])
        
        disagreements_prompt = f"""
        Przeanalizuj stanowiska różnych agentów i zidentyfikuj główne punkty niezgody:
        
        STANOWISKA AGENTÓW:
        {positions_summary}
        
        Zidentyfikuj 3-5 kluczowych obszarów, gdzie agenci się nie zgadzają.
        Format: lista punktów, jeden w każdej linii.
        """
        
        try:
            disagreements_response = await self.llm_client.chat_completion([{
                "role": "system",
                "content": "Jesteś moderatorem debaty. Identyfikujesz punkty sporne."
            }, {
                "role": "user",
                "content": disagreements_prompt
            }])
            
            disagreements = [d.strip() for d in disagreements_response.split('\n') if d.strip()]
            return disagreements[:5]
            
        except Exception as e:
            return [f"Błąd identyfikacji niezgody: {e}"]
    
    async def _conduct_cross_critiques(self, agent_responses: List[AgentResponse]) -> List[str]:
        """Przeprowadź krytykę wzajemną między agentami"""
        
        critiques = []
        
        # Każdy agent krytykuje odpowiedzi innych
        for i, critic_response in enumerate(agent_responses):
            for j, target_response in enumerate(agent_responses):
                if i != j:  # Nie krytykuj sam siebie
                    critique = await self._generate_cross_critique(
                        critic_response, target_response
                    )
                    if critique:
                        critiques.append(critique)
        
        return critiques[:10]  # Ogranicz do 10 najważniejszych krytyk
    
    async def _generate_cross_critique(
        self, 
        critic: AgentResponse, 
        target: AgentResponse
    ) -> str:
        """Wygeneruj krytykę jednego agenta wobec drugiego"""
        
        critique_prompt = f"""
        Jako {critic.agent_name}, skomentuj stanowisko {target.agent_name}:
        
        STANOWISKO {target.agent_name}: {target.response_content}
        
        Z perspektywy swojej roli ({critic.agent_role.value}), podaj krótką (2-3 zdania) konstruktywną krytykę lub komentarz.
        """
        
        try:
            critique = await self.llm_client.chat_completion([{
                "role": "system",
                "content": f"Jesteś {critic.agent_name}. Komentujesz stanowisko innego agenta."
            }, {
                "role": "user",
                "content": critique_prompt
            }])
            
            return f"{critic.agent_name} → {target.agent_name}: {critique}"
            
        except Exception as e:
            return None
    
    async def _find_consensus_areas(self, agent_responses: List[AgentResponse]) -> List[str]:
        """Znajdź obszary konsensusu między agentami"""
        
        consensus_prompt = f"""
        Przeanalizuj stanowiska agentów i znajdź obszary, gdzie się zgadzają:
        
        STANOWISKA:
        {chr(10).join([f"{r.agent_name}: {r.response_content[:150]}..." for r in agent_responses])}
        
        Zidentyfikuj 3-5 punktów wspólnych lub podobnych wniosków.
        Format: lista punktów konsensusu.
        """
        
        try:
            consensus_response = await self.llm_client.chat_completion([{
                "role": "system",
                "content": "Identyfikujesz obszary zgody i konsensusu."
            }, {
                "role": "user",
                "content": consensus_prompt
            }])
            
            consensus_areas = [c.strip() for c in consensus_response.split('\n') if c.strip()]
            return consensus_areas[:5]
            
        except Exception as e:
            return [f"Błąd identyfikacji konsensusu: {e}"]
    
    async def _summarize_debate(
        self, 
        agent_responses: List[AgentResponse],
        disagreements: List[str],
        critiques: List[str],
        consensus_areas: List[str],
        original_query: str
    ) -> str:
        """Podsumuj przebieg debaty"""
        
        summary_prompt = f"""
        Podsumuj przebieg wewnętrznej debaty agentów na temat: {original_query}
        
        UCZESTNICY: {', '.join([r.agent_name for r in agent_responses])}
        
        GŁÓWNE NIEZGODY:
        {chr(10).join(disagreements)}
        
        OBSZARY KONSENSUSU:  
        {chr(10).join(consensus_areas)}
        
        Napisz zwięzłe podsumowanie (150-250 słów) przebiegu debaty.
        """
        
        try:
            summary = await self.llm_client.chat_completion([{
                "role": "system",
                "content": "Jesteś sprawozdawcą debat. Tworzysz zwięzłe i obiektywne podsumowania."
            }, {
                "role": "user",
                "content": summary_prompt
            }])
            
            return summary
            
        except Exception as e:
            return f"Błąd podsumowania debaty: {e}"
    
    async def _synthesize_consensus(
        self, 
        agent_responses: List[AgentResponse],
        debate_results: Dict[str, Any],
        method: str
    ) -> ConsensusResult:
        """Syntetyzuj konsensus z odpowiedzi agentów"""
        
        if method == "weighted_synthesis":
            return await self._weighted_synthesis(agent_responses, debate_results)
        elif method == "democratic_vote":
            return await self._democratic_vote(agent_responses, debate_results)
        elif method == "expert_selection":
            return await self._expert_selection(agent_responses, debate_results)
        else:
            return await self._weighted_synthesis(agent_responses, debate_results)  # Default
    
    async def _weighted_synthesis(
        self, 
        agent_responses: List[AgentResponse],
        debate_results: Dict[str, Any]
    ) -> ConsensusResult:
        """Synteza ważona na podstawie confidence i wag agentów"""
        
        # Oblicz wagi dla każdego agenta
        total_weight = 0
        weighted_responses = []
        
        for response in agent_responses:
            agent_weight = self.agent_weights.get(response.agent_role, 1.0)
            combined_weight = agent_weight * response.confidence_score
            total_weight += combined_weight
            weighted_responses.append((response, combined_weight))
        
        # Stwórz syntezę
        synthesis_prompt = f"""
        Stwórz syntezę następujących perspektyw (z wagami):
        
        {chr(10).join([
            f"[Waga: {weight/total_weight:.2f}] {resp.agent_name}: {resp.response_content}"
            for resp, weight in weighted_responses
        ])}
        
        DEBATA: {debate_results.get('debate_summary', '')}
        
        Utwórz spójną, zbalansowaną odpowiedź (300-500 słów) która:
        1. Integruje najlepsze elementy z różnych perspektyw
        2. Uwzględnia wagi i pewność agentów
        3. Rozwiązuje główne niezgody konstruktywnie
        4. Zachowuje nuanse i złożoność problemu
        """
        
        try:
            synthesis_response = await self.llm_client.chat_completion([{
                "role": "system",
                "content": "Jesteś mistrzem syntezy. Tworzysz spójne całości z różnych perspektyw."
            }, {
                "role": "user",
                "content": synthesis_prompt
            }])
            
            # Oblicz siłę konsensusu
            consensus_strength = self._calculate_consensus_strength(agent_responses, debate_results)
            
            # Przygotuj rozkład pewności
            confidence_distribution = {
                resp.agent_role: resp.confidence_score for resp in agent_responses
            }
            
            return ConsensusResult(
                final_response=synthesis_response,
                consensus_strength=consensus_strength,
                participating_agents=[resp.agent_role for resp in agent_responses],
                integration_method="weighted_synthesis",
                confidence_distribution=confidence_distribution,
                disagreement_points=debate_results.get('disagreements', []),
                synthesis_quality=0.0,  # Będzie obliczone później
                emergence_level=0.0     # Będzie obliczone później
            )
            
        except Exception as e:
            # Fallback: wybierz najlepszą pojedynczą odpowiedź
            best_response = max(agent_responses, key=lambda r: r.confidence_score)
            return ConsensusResult(
                final_response=best_response.response_content,
                consensus_strength=0.5,
                participating_agents=[best_response.agent_role],
                integration_method="fallback_best",
                confidence_distribution={best_response.agent_role: best_response.confidence_score},
                disagreement_points=[f"Błąd syntezy: {e}"],
                synthesis_quality=0.3,
                emergence_level=0.0
            )
    
    def _calculate_consensus_strength(
        self, 
        agent_responses: List[AgentResponse],
        debate_results: Dict[str, Any]
    ) -> float:
        """Oblicz siłę osiągniętego konsensusu"""
        
        if not agent_responses:
            return 0.0
        
        # Bazowa siła na podstawie liczby agentów
        base_strength = min(len(agent_responses) / 5.0, 0.4)
        
        # Bonus za obszary konsensusu
        consensus_areas = debate_results.get('consensus_areas', [])
        consensus_bonus = min(len(consensus_areas) / 10.0, 0.3)
        
        # Malus za niezgody
        disagreements = debate_results.get('disagreements', [])
        disagreement_penalty = min(len(disagreements) / 10.0, 0.2)
        
        # Bonus za wysoką pewność agentów
        avg_confidence = sum(r.confidence_score for r in agent_responses) / len(agent_responses)
        confidence_bonus = avg_confidence * 0.3
        
        consensus_strength = base_strength + consensus_bonus + confidence_bonus - disagreement_penalty
        
        return max(0.0, min(1.0, consensus_strength))
    
    async def _evaluate_synthesis_quality(self, consensus: ConsensusResult) -> float:
        """Oceń jakość syntezy"""
        
        quality_prompt = f"""
        Oceń jakość następującej syntezy (skala 0-1):
        
        SYNTEZA: {consensus.final_response}
        
        KRYTERIA:
        - Spójność i logika
        - Kompletność odpowiedzi
        - Integracja różnych perspektyw
        - Praktyczna użyteczność
        - Jasność komunikacji
        
        Zwróć tylko liczbę od 0 do 1 (np. 0.75)
        """
        
        try:
            quality_response = await self.llm_client.chat_completion([{
                "role": "system",
                "content": "Jesteś ekspertem w ocenie jakości tekstów i syntez."
            }, {
                "role": "user",
                "content": quality_prompt
            }])
            
            # Wyciągnij liczbę z odpowiedzi
            import re
            numbers = re.findall(r'0\.\d+|1\.0|0|1', quality_response)
            if numbers:
                return float(numbers[0])
            else:
                return 0.5  # Fallback
                
        except Exception as e:
            return 0.5  # Fallback
    
    async def _detect_emergence_level(
        self, 
        agent_responses: List[AgentResponse],
        final_response: str
    ) -> float:
        """Wykryj poziom emergencji - czy powstała nowa wiedza z interakcji"""
        
        # Sprawdź, czy finalna odpowiedź zawiera elementy nieobecne w żadnej z pojedynczych odpowiedzi
        all_agent_content = " ".join([resp.response_content for resp in agent_responses])
        
        emergence_prompt = f"""
        Porównaj finalną syntezę z oryginalnymi odpowiedziami agentów:
        
        ORYGINALNE ODPOWIEDZI AGENTÓW:
        {all_agent_content[:1500]}...
        
        FINALNA SYNTEZA:
        {final_response}
        
        Oceń poziom emergencji (0-1): czy w syntezie pojawiły się nowe idee, połączenia lub wglądy, 
        które nie były obecne w żadnej z oryginalnych odpowiedzi?
        
        Zwróć tylko liczbę od 0 do 1.
        """
        
        try:
            emergence_response = await self.llm_client.chat_completion([{
                "role": "system",
                "content": "Analizujesz emergentne właściwości syntezy myśli."
            }, {
                "role": "user",
                "content": emergence_prompt
            }])
            
            # Wyciągnij liczbę
            import re
            numbers = re.findall(r'0\.\d+|1\.0|0|1', emergence_response)
            if numbers:
                return float(numbers[0])
            else:
                return 0.0
                
        except Exception as e:
            return 0.0
    
    async def _update_agent_weights(
        self, 
        agent_responses: List[AgentResponse],
        consensus: ConsensusResult
    ):
        """Aktualizuj wagi agentów na podstawie performance"""
        
        # Agenci z wyższą pewnością i lepszą syntezą dostają bonus
        for response in agent_responses:
            role = response.agent_role
            
            # Bonus za pewność
            confidence_bonus = (response.confidence_score - 0.5) * 0.1
            
            # Bonus za wkład do wysokiej jakości syntezy
            quality_bonus = consensus.synthesis_quality * 0.05
            
            # Aktualizuj wagę z learning rate
            learning_rate = 0.05
            weight_change = (confidence_bonus + quality_bonus) * learning_rate
            
            self.agent_weights[role] = max(0.1, min(2.0, self.agent_weights[role] + weight_change))
            
            # Aktualizuj statystyki performance
            if response.confidence_score > 0.6:
                self.orchestration_stats["agent_performance"][role]["success"] += 1
    
    async def get_orchestration_report(self) -> Dict[str, Any]:
        """Pobierz raport stanu orkiestry"""
        
        return {
            "stats": self.orchestration_stats,
            "agent_weights": {role.value: weight for role, weight in self.agent_weights.items()},
            "recent_sessions": len([s for s in self.interaction_history[-10:]]),
            "agent_personas": {
                role.value: {
                    "name": persona.name,
                    "specialties": persona.specialties,
                    "current_weight": self.agent_weights[role]
                }
                for role, persona in self.agent_personas.items()
            },
            "performance_summary": {
                role.value: {
                    "success_rate": (perf["success"] / perf["total"]) if perf["total"] > 0 else 0,
                    "total_uses": perf["total"]
                }
                for role, perf in self.orchestration_stats["agent_performance"].items()
            }
        }

# Globalna instancja orkiestry
_multi_agent_orchestrator = None

def get_multi_agent_orchestrator() -> MultiAgentOrchestrator:
    """Pobierz globalną instancję orkiestry wieloagentowej"""
    global _multi_agent_orchestrator
    if _multi_agent_orchestrator is None:
        _multi_agent_orchestrator = MultiAgentOrchestrator()
    return _multi_agent_orchestrator

async def multi_agent_response(
    query: str,
    context: Dict[str, Any] = None,
    agents: List[str] = None,
    method: str = "weighted_synthesis"
) -> ConsensusResult:
    """
    Główna funkcja do generowania wieloagentowej odpowiedzi
    
    Args:
        query: Zapytanie użytkownika
        context: Kontekst zapytania  
        agents: Lista ról agentów (strings)
        method: Metoda konsensusu
        
    Returns:
        ConsensusResult: Wynik konsensusu wieloagentowego
    """
    orchestrator = get_multi_agent_orchestrator()
    
    # Konwersja stringów na AgentRole
    if agents:
        active_agents = []
        for agent_str in agents:
            try:
                role = AgentRole(agent_str.lower())
                active_agents.append(role)
            except ValueError:
                log_warning(f"[MULTI_AGENT] Nieznana rola agenta: {agent_str}")
    else:
        active_agents = None
    
    return await orchestrator.orchestrate_multi_agent_response(
        query, context, active_agents, method
    )

# Test funkcji
if __name__ == "__main__":
    async def test_multi_agent():
        """Test systemu wieloagentowego"""
        
        queries = [
            "Jak rozwiązać konflikt między kreatywnością a praktycznością w projekcie?",
            "Czy sztuczna inteligencja zastąpi ludzką pracę?",
            "Jaki jest sens życia?"
        ]
        
        print("🧩 TEST SYSTEMU WIELOAGENTOWEGO")
        print("=" * 60)
        
        for i, query in enumerate(queries, 1):
            print(f"\n🔍 TEST {i}: {query}")
            print("-" * 50)
            
            result = await multi_agent_response(
                query=query,
                context={"test_mode": True},
                agents=["analyst", "creator", "critic", "philosopher"],
                method="weighted_synthesis"
            )
            
            print(f"✅ Konsensus: {result.consensus_strength:.2f}")
            print(f"⚡ Jakość: {result.synthesis_quality:.2f}")
            print(f"🚀 Emergencja: {result.emergence_level:.2f}")
            print(f"👥 Agenci: {[role.value for role in result.participating_agents]}")
            print(f"📝 Odpowiedź: {result.final_response[:300]}...")
            
            if result.disagreement_points:
                print(f"⚡ Niezgody: {len(result.disagreement_points)}")
        
        # Raport orkiestry
        orchestrator = get_multi_agent_orchestrator()
        report = await orchestrator.get_orchestration_report()
        
        print(f"\n📊 RAPORT ORKIESTRY:")
        print(f"Sesje: {report['stats']['total_sessions']}")
        print(f"Średni konsensus: {report['stats']['avg_consensus_strength']:.2f}")
        print(f"Zdarzenia emergencji: {report['stats']['emergence_events']}")
    
    # Uruchom test
    asyncio.run(test_multi_agent())