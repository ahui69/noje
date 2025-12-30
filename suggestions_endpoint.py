#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Proactive Suggestions Endpoint - Endpoint FastAPI dla proaktywnych sugestii
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any

from core.auth import auth_dependency
from advanced_proactive import (
    get_proactive_suggestions,
    inject_suggestions_to_prompt,
    suggestion_generator,
)

# Utwórz router
router = APIRouter(
    prefix="/api/suggestions",
    tags=["Proactive Suggestions"],
    responses={404: {"description": "Not found"}},
)


@router.post("/generate", summary="Generuje proaktywne sugestie")
async def generate_suggestions(
    data: Dict[str, Any] = Body(...),
    _: bool = Depends(auth_dependency)
):
    """Generuje proaktywne sugestie dla wiadomości użytkownika."""
    try:
        user_id = data.get("user_id", "default_user")
        message = data.get("message")
        
        if not message:
            raise HTTPException(status_code=400, detail="Brakujące pole: message")
        
        conversation_history = data.get("conversation_history", [])
        last_ai_response = data.get("last_ai_response", "")
        force = data.get("force", False)
        
        # Generuj sugestie
        suggestions = await get_proactive_suggestions(
            user_id=user_id,
            message=message,
            conversation_history=conversation_history,
            last_ai_response=last_ai_response,
            force=force
        )
        
        return {
            "status": "success",
            "suggestions": suggestions
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.post("/inject", summary="Dodaje sugestie do promptu")
async def inject_suggestions(
    data: Dict[str, Any] = Body(...),
    _: bool = Depends(auth_dependency)
):
    """Dodaje sugestie do promptu systemowego."""
    try:
        base_prompt = data.get("base_prompt", "")
        suggestions = data.get("suggestions", [])
        
        if not base_prompt:
            raise HTTPException(status_code=400, detail="Brakujące pole: base_prompt")
        
        enhanced_prompt = inject_suggestions_to_prompt(base_prompt, suggestions)
        
        return {
            "status": "success",
            "enhanced_prompt": enhanced_prompt
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/stats", summary="Pobiera statystyki sugestii")
async def get_stats(_: bool = Depends(auth_dependency)):
    """Pobiera statystyki generowania sugestii."""
    try:
        stats = suggestion_generator.get_suggestion_stats()
        conv_summary = suggestion_generator.conversation_analyzer.get_conversation_summary()
        
        return {
            "status": "success",
            "suggestion_stats": stats,
            "conversation_summary": conv_summary
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.post("/analyze", summary="Analizuje wiadomość")
async def analyze_message(
    data: Dict[str, Any] = Body(...),
    _: bool = Depends(auth_dependency)
):
    """Analizuje wiadomość bez generowania sugestii."""
    try:
        user_id = data.get("user_id", "default_user")
        message = data.get("message")
        
        if not message:
            raise HTTPException(status_code=400, detail="Brakujące pole: message")
        
        analysis = suggestion_generator.conversation_analyzer.analyze_message(user_id, message)
        
        return {
            "status": "success",
            "analysis": analysis
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
