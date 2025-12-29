#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELF-REFLECTION ENDPOINT - Dynamiczna Rekurencja Umysłowa
AI sam ocenia swoje odpowiedzi i je poprawia
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from enum import Enum

from core.auth import verify_token
from core.self_reflection import (
    get_reflection_engine, reflect_on_response,
    ReflectionDepth, SelfReflectionEngine
)
from core.helpers import log_info, log_error

# Utwórz router
router = APIRouter(
    prefix="/api/reflection",
    tags=["Self-Reflection"],
    responses={404: {"description": "Not found"}},
)


class ReflectionRequest(BaseModel):
    query: str
    response: str
    depth: Optional[str] = "MEDIUM"  # SURFACE, MEDIUM, DEEP, PROFOUND, TRANSCENDENT
    user_id: Optional[str] = "system"


class AdaptiveReflectionRequest(BaseModel):
    query: str
    response: str
    user_id: Optional[str] = "system"


@router.post("/reflect", summary="Przeprowadź refleksję nad odpowiedzią")
async def reflect(
    request: ReflectionRequest,
    auth=Depends(verify_token)
):
    """
    Przeprowadza pełną refleksję nad odpowiedzią AI.
    
    Args:
        request: query, response, depth, user_id
        
    Returns:
        Kompletny cykl refleksji z poprawioną odpowiedzią
    """
    try:
        # Konwertuj depth string na enum
        try:
            depth_enum = ReflectionDepth[request.depth.upper()]
        except (KeyError, AttributeError):
            depth_enum = ReflectionDepth.MEDIUM
        
        # Przeprowadź refleksję
        cycle = await reflect_on_response(
            query=request.query,
            response=request.response,
            depth=depth_enum,
            user_id=request.user_id
        )
        
        return {
            "ok": True,
            "reflection_cycle": {
                "input_query": cycle.input_query,
                "initial_response": cycle.initial_response,
                "evaluation": cycle.evaluation,
                "meta_commentary": cycle.meta_commentary,
                "improved_response": cycle.improved_response,
                "reflection_score": cycle.reflection_score,
                "cycle_time": cycle.cycle_time,
                "depth_achieved": cycle.depth_achieved,
                "insights_gained": cycle.insights_gained,
                "corrections_made": cycle.corrections_made
            },
            "message": f"Refleksja poziom {depth_enum.name} - score: {cycle.reflection_score:.2f}"
        }
        
    except Exception as e:
        log_error(f"Reflection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/adaptive-reflect", summary="Adaptacyjna refleksja (auto-depth)")
async def adaptive_reflect(
    request: AdaptiveReflectionRequest,
    auth=Depends(verify_token)
):
    """
    Przeprowadza refleksję z automatycznym wyborem głębokości.
    
    Args:
        request: query, response, user_id
        
    Returns:
        Refleksję z optymalną głębokością
    """
    try:
        engine = get_reflection_engine()
        
        # Automatyczny wybór głębokości
        optimal_depth = await engine.adaptive_depth_selection(
            query=request.query
        )
        
        # Przeprowadź refleksję
        cycle = await reflect_on_response(
            query=request.query,
            response=request.response,
            depth=optimal_depth,
            user_id=request.user_id
        )
        
        return {
            "ok": True,
            "selected_depth": optimal_depth.name,
            "reflection_cycle": {
                "input_query": cycle.input_query,
                "initial_response": cycle.initial_response,
                "evaluation": cycle.evaluation,
                "meta_commentary": cycle.meta_commentary,
                "improved_response": cycle.improved_response,
                "reflection_score": cycle.reflection_score,
                "cycle_time": cycle.cycle_time,
                "depth_achieved": cycle.depth_achieved,
                "insights_gained": cycle.insights_gained,
                "corrections_made": cycle.corrections_made
            },
            "message": f"Adaptacyjna refleksja: {optimal_depth.name} - score: {cycle.reflection_score:.2f}"
        }
        
    except Exception as e:
        log_error(f"Adaptive reflection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/depths", summary="Pobiera dostępne poziomy refleksji")
async def get_reflection_depths(auth=Depends(verify_token)):
    """
    Pobiera listę dostępnych poziomów głębokości refleksji.
    
    Returns:
        Lista poziomów z opisami
    """
    try:
        depths = {
            "SURFACE": {
                "level": 1,
                "description": "Podstawowa ewaluacja - dokładność, jasność, kompletność"
            },
            "MEDIUM": {
                "level": 2,
                "description": "Analiza + korekta - logika, kontekst, użyteczność"
            },
            "DEEP": {
                "level": 3,
                "description": "Głęboka introspekcja - analiza wielowymiarowa"
            },
            "PROFOUND": {
                "level": 4,
                "description": "Filozoficzna refleksja - ontologia, epistemologia, aksjologia"
            },
            "TRANSCENDENT": {
                "level": 5,
                "description": "Transcendentna analiza - przekroczenie granic myśli"
            }
        }
        
        return {
            "ok": True,
            "depths": depths,
            "message": "Dostępne poziomy refleksji"
        }
        
    except Exception as e:
        log_error(f"Depths error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", summary="Statystyki refleksji")
async def get_reflection_stats(auth=Depends(verify_token)):
    """
    Pobiera statystyki procesu refleksji.
    
    Returns:
        Szczegółowe statystyki refleksji
    """
    try:
        engine = get_reflection_engine()
        stats = await engine.get_reflection_summary()
        
        return {
            "ok": True,
            "stats": stats,
            "message": "Statystyki procesu refleksji"
        }
        
    except Exception as e:
        log_error(f"Reflection stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/meta-patterns", summary="Meta-wzorce myślenia")
async def get_meta_patterns(auth=Depends(verify_token)):
    """
    Pobiera zidentyfikowane meta-wzorce w procesie myślenia.
    
    Returns:
        Meta-wzorce i insights
    """
    try:
        engine = get_reflection_engine()
        
        return {
            "ok": True,
            "meta_patterns": engine.meta_patterns,
            "improvement_rate": engine.improvement_rate,
            "total_reflections": len(engine.reflection_history),
            "message": "Meta-wzorce procesu myślowego"
        }
        
    except Exception as e:
        log_error(f"Meta-patterns error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", summary="Historia refleksji")
async def get_reflection_history(
    limit: int = 10,
    auth=Depends(verify_token)
):
    """
    Pobiera historię ostatnich refleksji.
    
    Args:
        limit: Liczba ostatnich refleksji do pobrania
        
    Returns:
        Historia cykli refleksji
    """
    try:
        engine = get_reflection_engine()
        recent_history = engine.reflection_history[-limit:] if engine.reflection_history else []
        
        history_data = []
        for cycle in recent_history:
            history_data.append({
                "query": cycle.input_query[:100] + "..." if len(cycle.input_query) > 100 else cycle.input_query,
                "reflection_score": cycle.reflection_score,
                "depth": cycle.depth_achieved,
                "cycle_time": cycle.cycle_time,
                "insights_count": len(cycle.insights_gained),
                "corrections_count": len(cycle.corrections_made)
            })
        
        return {
            "ok": True,
            "history": history_data,
            "total_reflections": len(engine.reflection_history),
            "message": f"Historia ostatnich {len(history_data)} refleksji"
        }
        
    except Exception as e:
        log_error(f"Reflection history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))