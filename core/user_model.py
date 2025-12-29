#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/user_model.py - Moduł do budowania modelu poznawczego użytkownika
"Szachista" - przewidywanie następnego ruchu.
"""

import re
from collections import Counter
from typing import Dict, List, Any, Optional

class UserModel:
    """
    Buduje i utrzymuje dynamiczny profil użytkownika na podstawie jego interakcji.
    """
    def __init__(self):
        # Przechowuje profile w pamięci. W przyszłości można to przenieść do bazy danych.
        # { user_id: { "topics": Counter(), "style": Counter(), "intent_history": [] } }
        self.user_profiles: Dict[str, Dict[str, Any]] = {}

    def get_or_create_profile(self, user_id: str) -> Dict[str, Any]:
        """Pobiera profil użytkownika lub tworzy nowy, jeśli nie istnieje."""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                "topics": Counter(),          # Najczęstsze tematy (np. 'python', 'api', 'docker')
                "style": Counter(),           # Styl komunikacji (np. 'pytający', 'rozkazujący')
                "intent_history": [],         # Ostatnie intencje
                "message_count": 0
            }
        return self.user_profiles[user_id]

    def update_profile(self, user_id: str, message: str, detected_intent: Optional[str] = None):
        """Aktualizuje profil użytkownika na podstawie nowej wiadomości."""
        profile = self.get_or_create_profile(user_id)
        
        profile["message_count"] += 1
        
        # 1. Analiza tematów (proste słowa kluczowe)
        tokens = set(re.findall(r'\b\w{3,}\b', message.lower()))
        tech_keywords = {'python', 'docker', 'api', 'fastapi', 'test', 'kod', 'git', 'bazę'}
        casual_keywords = {'jak', 'czy', 'możesz', 'pomóc', 'myślisz', 'fajne'}
        
        profile["topics"].update([t for t in tokens if t in tech_keywords])

        # 2. Analiza stylu
        if '?' in message:
            profile["style"]["pytający"] += 1
        if message.lower().startswith(('zrób', 'napisz', 'stwórz', 'wykonaj')):
            profile["style"]["rozkazujący"] += 1
        
        # 3. Historia intencji
        if detected_intent:
            profile["intent_history"].append(detected_intent)
            if len(profile["intent_history"]) > 5:
                profile["intent_history"].pop(0)

    def predict_next_action(self, user_id: str, last_message: str) -> Optional[str]:
        """
        Przewiduje następną akcję lub pytanie użytkownika ("Ruch Szachisty").
        """
        profile = self.get_or_create_profile(user_id)
        
        if profile["message_count"] < 3:
            return None # Potrzebujemy więcej danych, żeby cokolwiek przewidzieć

        # --- Proste reguły predykcyjne ---

        # Reguła 1: Jeśli user pyta o listowanie czegoś, prawdopodobnie zapyta o szczegóły jednego elementu.
        if re.search(r'\b(list|pokaż|jakie)\s+(pliki|katalogi|testy)\b', last_message.lower()):
            return "prośba o szczegóły jednego z wylistowanych elementów"

        # Reguła 2: Jeśli user prosi o stworzenie pliku, prawdopodobnie będzie chciał zobaczyć jego zawartość.
        if re.search(r'\b(stwórz|zapisz)\s+plik\b', last_message.lower()):
            return "prośba o weryfikację zawartości nowo utworzonego pliku"

        # Reguła 3: Jeśli user pyta o podstawy (np. "co to jest FastAPI"), prawdopodobnie zapyta o prosty przykład.
        if re.search(r'\b(co to jest|jak działa)\s+[a-zA-Z0-9]+\b', last_message.lower()) and "przykład" not in last_message.lower():
            return "prośba o prosty przykład kodu"
            
        # Reguła 4: Na podstawie najczęstszego tematu
        if profile["topics"]:
            most_common_topic = profile["topics"].most_common(1)[0][0]
            if most_common_topic == "python" and "test" not in last_message.lower():
                return f"dalsze pytania o Pythonie, być może dotyczące testowania kodu"

        return None

# Tworzymy jedną, globalną instancję managera profili
user_model_manager = UserModel()
