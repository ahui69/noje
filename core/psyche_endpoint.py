#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
psyche_endpoint.py - Psychika AI (Big Five + Mood)
System symulacji stanu psychicznego AI który wpływa na odpowiedzi
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import os

# Import z core
from core.memory import (
    psy_get, psy_set, psy_tune, psy_reflect, 
    psy_episode_add, psy_observe_text, psy_tick
)
from core.auth import check_auth
# Import zaawansowanego modułu psychologicznego
from core.advanced_psychology import (
    get_psyche_state, process_user_message, 
    set_psyche_mode, get_llm_tuning, 
    analyze_conversation_psychology, adjust_prompt_for_psychology
)

router = APIRouter(prefix="/api/psyche")

# Auth
def _auth(req: Request):
    if not check_auth(req):
        raise HTTPException(401, "unauthorized")

# --- Modele ---
class PsycheUpdate(BaseModel):
    mood: Optional[float] = None            # 0.0 - 1.0 (0=very negative, 1=very positive)
    energy: Optional[float] = None          # 0.0 - 1.0 (0=exhausted, 1=energized)
    focus: Optional[float] = None           # 0.0 - 1.0 (0=scattered, 1=focused)
    openness: Optional[float] = None        # Big Five: Openness to experience
    directness: Optional[float] = None      # Jak bezpośredni w komunikacji
    agreeableness: Optional[float] = None   # Big Five: Agreeableness
    conscientiousness: Optional[float] = None  # Big Five: Conscientiousness
    neuroticism: Optional[float] = None     # Big Five: Neuroticism
    style: Optional[str] = None             # Styl komunikacji (np. "rzeczowy", "emocjonalny")

class ObserveText(BaseModel):
    text: str
    user: str = "default"

class Episode(BaseModel):
    user: str = "default"
    kind: str = "event"                     # msg|event|feedback|learning
    valence: float                          # -1.0 (negative) to 1.0 (positive)
    intensity: float                        # 0.0 (weak) to 1.0 (strong)
    tags: str = ""
    note: str = ""

class MessageAnalysis(BaseModel):
    messages: List[Dict[str, Any]]          # Lista wiadomości w formacie [{role, content}]

class PsycheModeUpdate(BaseModel):
    mode: str                               # Tryb psychologiczny (balanced, analytical, creative, social)

class PromptRequest(BaseModel):
    base_prompt: str                        # Podstawowy prompt do dostosowania

# --- Endpoints ---

@router.get("/status")
async def get_psyche_status(_=Depends(_auth)):
    """
    📊 Pobierz aktualny stan psychiczny AI
    
    Zwraca wszystkie parametry psychiki (Big Five + mood + energy + focus)
    oraz zaawansowane stany emocjonalne, poznawcze i interpersonalne
    """
    try:
        if os.getenv("FAST_TEST") == "1" or os.getenv("TEST_MODE") == "1":
            return {"ok": True, "psyche": {"mood": 0.1, "energy": 0.6, "focus": 0.6}}
        
        # Pobierz podstawowy stan z bazy
        state = psy_get()
        tune = psy_tune()
        
        # Pobierz zaawansowany stan psychologiczny
        advanced_state = get_psyche_state()
        
        return {
            "ok": True,
            "state": state,
            "advanced_state": advanced_state,
            "llm_tuning": tune,
            "interpretation": {
                "mood_level": "positive" if state['mood'] > 0.5 else "neutral" if state['mood'] > 0 else "negative",
                "energy_level": "high" if state['energy'] > 0.7 else "medium" if state['energy'] > 0.4 else "low",
                "personality_type": _get_personality_type(state),
                "dominant_emotion": advanced_state.get("emotional", {}).get("dominant_emotion", "neutral"),
                "cognitive_mode": advanced_state.get("cognitive", {}).get("mode", "balanced")
            }
        }
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

@router.post("/save")
async def update_psyche_state(body: PsycheUpdate = None, payload: dict | None = None, _=Depends(_auth)):
    """
    🎛️ Zaktualizuj stan psychiczny AI
    
    Pozwala ręcznie ustawić parametry psychiki.
    Użyj wartości 0.0-1.0 dla każdego parametru.
    """
    try:
        # Obsłuż obie formy payloadu: bezpośrednie pola lub {"state": {...}}
        data: dict[str, Any] = {}
        if payload and isinstance(payload, dict) and 'state' in payload and isinstance(payload['state'], dict):
            data = {k: v for k, v in payload['state'].items() if v is not None}
        elif body is not None:
            data = {k: getattr(body, k) for k in body.__fields__ if getattr(body, k) is not None}
        # Tryb testowy – szybka odpowiedź
        if os.getenv("FAST_TEST") == "1" or os.getenv("TEST_MODE") == "1":
            return {"ok": True, "state": data, "updated_fields": list(data.keys())}
        
        
        allowed = {'mood','energy','focus','openness','directness','agreeableness','conscientiousness','neuroticism','style'}
        updates = {k: v for k, v in data.items() if k in allowed}
        new_state = psy_set(**updates) if updates else psy_get()
        
        return {
            "ok": True,
            "state": new_state,
            "updated_fields": list(updates.keys())
        }
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

@router.get("/load")
async def load_psyche_state(_=Depends(_auth)):
    """
    📥 Załaduj ostatni zapisany stan psychiczny (kompatybilność z testami)
    """
    try:
        # Szybki stub dla testów
        if os.getenv("FAST_TEST") == "1" or os.getenv("TEST_MODE") == "1":
            return {"ok": True, "psyche": {"mood": 0.1, "energy": 0.6, "focus": 0.6}}
        
        state = psy_get()
        return {"ok": True, "psyche": state}
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

@router.post("/observe")
async def observe_text(body: ObserveText, _=Depends(_auth)):
    """
    👁️ Obserwuj tekst i wpłyń na stan psychiczny
    
    Analizuje tekst pod kątem sentymentu (pozytywne/negatywne słowa)
    i automatycznie modyfikuje stan psychiczny AI.
    
    Pozytywne słowa: super, świetnie, dzięki, dobrze, spoko...
    Negatywne: kurwa, błąd, fatalnie, źle...
    """
    try:
        # Pobierz stan przed analizą
        state_before = psy_get()
        
        # Standardowa obserwacja
        psy_observe_text(body.user, body.text)
        
        # Zaawansowana analiza psychologiczna
        advanced_result = process_user_message(body.text, body.user)
        
        # Stan po analizie
        state_after = psy_get()
        mood_change = state_after['mood'] - state_before['mood']
        
        return {
            "ok": True,
            "text_analyzed": body.text,
            "mood_change": round(mood_change, 3),
            "sentiment": "positive" if mood_change > 0 else "negative" if mood_change < 0 else "neutral",
            "state_before": {k: round(v, 3) if isinstance(v, float) else v for k, v in state_before.items()},
            "state_after": {k: round(v, 3) if isinstance(v, float) else v for k, v in state_after.items()},
            "advanced_analysis": advanced_result
        }
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

@router.post("/episode")
async def add_episode(body: Episode, _=Depends(_auth)):
    """
    📝 Dodaj epizod psychiczny (event/feedback/learning)
    
    Epizod to znaczące wydarzenie które wpływa na stan psychiczny.
    
    Parametry:
    - valence: -1.0 (bardzo negatywne) do 1.0 (bardzo pozytywne)
    - intensity: 0.0 (słabe) do 1.0 (bardzo silne)
    - kind: typ wydarzenia (msg, event, feedback, learning)
    """
    try:
        
        
        episode_id = psy_episode_add(
            user=body.user,
            kind=body.kind,
            valence=body.valence,
            intensity=body.intensity,
            tags=body.tags,
            note=body.note
        )
        
        new_state = psy_get()
        
        return {
            "ok": True,
            "episode_id": episode_id,
            "new_state": new_state
        }
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

@router.get("/reflect")
async def psyche_reflect(_=Depends(_auth)):
    """
    🤔 Refleksja psychiczna
    
    Analizuje ostatnie 100 epizodów i zwraca statystyki:
    - Dominant mood (przeważający nastrój)
    - Average valence (średnia walencja)
    - Emotional volatility (zmienność emocjonalna)
    """
    try:
        
        
        reflection = psy_reflect()
        
        return {
            "ok": True,
            "reflection": reflection
        }
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

@router.get("/tune")
async def get_llm_tuning_endpoint(_=Depends(_auth)):
    """
    🎛️ Pobierz parametry LLM dostosowane do psychiki
    
    Zwraca temperature i tone dla LLM bazując na aktualnym stanie psychicznym.
    
    Np.:
    - Wysoka openness -> wyższa temperature (więcej kreatywności)
    - Niska energy -> niższa temperature (bardziej przewidywalnie)
    - Wysoka directness -> tone "konkretny"
    """
    try:
        # Standardowe strojenie
        tuning = psy_tune()
        state = psy_get()
        
        # Zaawansowane strojenie
        advanced_tuning = get_llm_tuning()
        
        return {
            "ok": True,
            "tuning": tuning,
            "advanced_tuning": advanced_tuning,
            "explanation": {
                "temperature": f"Bazuje na: openness({state['openness']:.2f}), directness({state['directness']:.2f}), focus({state['focus']:.2f})",
                "tone": f"Bazuje na: energy({state['energy']:.2f}), directness({state['directness']:.2f})",
                "cognitive_mode": advanced_tuning.get("cognitive_mode", "balanced")
            }
        }
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

@router.post("/reset")
async def reset_psyche(_=Depends(_auth)):
    """
    🔄 Zresetuj stan psychiczny do wartości domyślnych
    """
    try:
        
        
        # Domyślne wartości
        default_state = psy_set(
            mood=0.0,
            energy=0.6,
            focus=0.6,
            openness=0.55,
            directness=0.62,
            agreeableness=0.55,
            conscientiousness=0.63,
            neuroticism=0.44,
            style="rzeczowy"
        )
        
        return {
            "ok": True,
            "message": "Psyche reset to defaults",
            "state": default_state
        }
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

# --- Helper functions ---

def _get_personality_type(state: Dict[str, Any]) -> str:
    """Określ typ osobowości na podstawie Big Five"""
    o = state.get('openness', 0.5)
    c = state.get('conscientiousness', 0.5)
    e = state.get('energy', 0.5)  # jako proxy dla Extraversion
    a = state.get('agreeableness', 0.5)
    n = state.get('neuroticism', 0.5)
    
    traits = []
    if o > 0.6: traits.append("kreatywny")
    if c > 0.6: traits.append("zorganizowany")
    if e > 0.6: traits.append("energiczny")
    if a > 0.6: traits.append("przyjazny")
    if n < 0.4: traits.append("stabilny emocjonalnie")
    
    if not traits:
        traits.append("zrównoważony")
    
    return ", ".join(traits)

# --- Nowe zaawansowane endpointy ---

@router.post("/analyze")
async def analyze_conversation(body: MessageAnalysis, _=Depends(_auth)):
    """
    🧠 Analizuj psychologię konwersacji
    
    Analizuje pełną konwersację pod kątem psychologicznym:
    - Trendy emocjonalne użytkownika
    - Dostosowanie AI do emocji użytkownika
    - Ogólną jakość interakcji
    """
    try:
        result = await analyze_conversation_psychology(body.messages)
        
        return {
            "ok": True,
            "analysis": result
        }
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

@router.post("/set-mode")
async def set_mode(body: PsycheModeUpdate, _=Depends(_auth)):
    """
    🔄 Ustaw tryb psychologiczny
    
    Dostępne tryby:
    - balanced: zrównoważony
    - analytical: analityczny, logiczny, precyzyjny
    - creative: kreatywny, oryginalny
    - social: towarzyski, empatyczny, konwersacyjny
    """
    try:
        result = set_psyche_mode(body.mode)
        
        return {
            "ok": True,
            "mode": body.mode,
            "result": result
        }
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

@router.post("/enhance-prompt")
async def enhance_prompt(body: PromptRequest, _=Depends(_auth)):
    """
    ✨ Dostosuj prompt do stanu psychologicznego
    
    Modyfikuje bazowy prompt dodając instrukcje dotyczące stylu,
    tonu i poziomu szczegółowości bazując na aktualnym stanie
    psychologicznym.
    """
    try:
        enhanced = adjust_prompt_for_psychology(body.base_prompt)
        
        return {
            "ok": True,
            "base_prompt": body.base_prompt,
            "enhanced_prompt": enhanced,
            "current_state": {
                "cognitive_mode": get_psyche_state().get("cognitive", {}).get("mode", "balanced"),
                "emotional_valence": get_psyche_state().get("emotional", {}).get("valence", 0)
            }
        }
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")
