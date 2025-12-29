#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test for Advanced Proactive Suggestions System
"""

import os
import sys
import asyncio
import json
from typing import List, Dict, Any

# Dodaj katalog główny do ścieżki Pythona
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Import proaktywnych sugestii
from advanced_proactive import (
    get_proactive_suggestions,
    inject_suggestions_to_prompt,
    suggestion_generator
)


async def test_proactive_suggestions():
    """Test głównych funkcji proaktywnych sugestii"""
    print("=" * 70)
    print("TEST SYSTEMU PROAKTYWNYCH SUGESTII")
    print("=" * 70)
    
    user_id = "test_user"
    
    # Test 1: Analiza wiadomości programistycznej
    print("\n[TEST 1] Wiadomość związana z programowaniem")
    message1 = "Mam problem z moim kodem Pythona, wyskakuje mi błąd ImportError. Co mam zrobić?"
    conversation1 = [
        {"role": "user", "content": "Czy możesz mi pomóc z kodem?"},
        {"role": "assistant", "content": "Oczywiście, chętnie pomogę. Jaki masz problem?"},
        {"role": "user", "content": message1}
    ]
    
    suggestions1 = await get_proactive_suggestions(
        user_id=user_id,
        message=message1,
        conversation_history=conversation1
    )
    
    print(f"Znaleziono {len(suggestions1)} sugestii:")
    for i, sugg in enumerate(suggestions1, 1):
        print(f"  {i}. {sugg['text']} (score: {sugg['score']:.2f})")
    
    # Test 2: Analiza wiadomości związanej z podróżami
    print("\n[TEST 2] Wiadomość związana z podróżami")
    message2 = "Szukam dobrego hotelu w Krakowie na weekend. Gdzie polecasz się zatrzymać?"
    conversation2 = [
        {"role": "user", "content": "Planuję wyjazd do Krakowa"},
        {"role": "assistant", "content": "Kraków to świetny wybór! Co chciałbyś wiedzieć o tym mieście?"},
        {"role": "user", "content": message2}
    ]
    
    suggestions2 = await get_proactive_suggestions(
        user_id=user_id,
        message=message2,
        conversation_history=conversation2
    )
    
    print(f"Znaleziono {len(suggestions2)} sugestii:")
    for i, sugg in enumerate(suggestions2, 1):
        print(f"  {i}. {sugg['text']} (score: {sugg['score']:.2f})")
    
    # Test 3: Test injekcji sugestii do promptu
    print("\n[TEST 3] Injekcja sugestii do promptu")
    base_prompt = "Jesteś pomocnym asystentem. Odpowiadaj na pytania użytkownika w sposób rzeczowy i konkretny."
    enhanced_prompt = inject_suggestions_to_prompt(base_prompt, suggestions2)
    
    print("Oryginalny prompt:")
    print(f"  {base_prompt}")
    print("\nPrompt z sugestią:")
    print(f"  {enhanced_prompt}")
    
    # Test 4: Analiza kontekstu konwersacji
    print("\n[TEST 4] Analiza kontekstu konwersacji")
    analysis = suggestion_generator.conversation_analyzer.analyze_message(user_id, message2)
    print("Wynik analizy:")
    print(f"  Główny temat: {analysis.get('main_topic')}")
    print(f"  Tematy: {analysis.get('topics')}")
    print(f"  Główna intencja: {analysis.get('main_intent')}")
    print(f"  Intencje: {analysis.get('intents')}")
    print(f"  Skupiona konwersacja: {analysis.get('is_focused')}")
    print(f"  Nieformalna konwersacja: {analysis.get('is_casual')}")
    
    # Test 5: Podsumowanie konwersacji
    print("\n[TEST 5] Podsumowanie konwersacji")
    summary = suggestion_generator.conversation_analyzer.get_conversation_summary()
    print("Podsumowanie:")
    print(f"  Dominujący temat: {summary.get('dominant_topic')}")
    print(f"  Dominująca intencja: {summary.get('dominant_intent')}")
    print(f"  Złożoność tematów: {summary.get('topic_complexity')}")
    print(f"  Złożoność intencji: {summary.get('intent_complexity')}")
    print(f"  Liczba wiadomości: {summary.get('message_count')}")
    
    print("\n[ZAKOŃCZONO] Wszystkie testy przeszły pomyślnie")


if __name__ == "__main__":
    # Uruchom test
    asyncio.run(test_proactive_suggestions())