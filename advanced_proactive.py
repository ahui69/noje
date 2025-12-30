#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Warstwa zgodności dla `core.advanced_proactive` zapewniająca działanie istniejących
importów `advanced_proactive` w routerach i testach bez fallbacków ani atrap.
"""

from core.advanced_proactive import (
    ConversationAnalyzer,
    ProactiveSuggestionGenerator,
    analyze_context,
    embed_text,
    get_proactive_engine,
    get_proactive_suggestions,
    get_psyche_state,
    get_smart_suggestions,
    inject_suggestions_to_prompt,
    ltm_search_hybrid,
    process_user_message,
    stm_get_context,
    suggestion_generator,
    user_model_manager,
)

__all__ = [
    "ConversationAnalyzer",
    "ProactiveSuggestionGenerator",
    "analyze_context",
    "embed_text",
    "get_proactive_engine",
    "get_proactive_suggestions",
    "get_psyche_state",
    "get_smart_suggestions",
    "inject_suggestions_to_prompt",
    "ltm_search_hybrid",
    "process_user_message",
    "stm_get_context",
    "suggestion_generator",
    "user_model_manager",
]
