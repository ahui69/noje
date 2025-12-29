#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vision & TTS Module Tests
"""

import pytest
import os


class TestVisionProvider:
    """Test vision_provider.py"""
    
    def test_vision_imports(self):
        """Test vision provider imports"""
        from vision_provider import analyze_image_universal
        assert callable(analyze_image_universal)
    
    @pytest.mark.asyncio
    async def test_vision_with_mock_image(self, test_image_base64):
        """Test vision analysis with mock image"""
        from vision_provider import analyze_image_universal
        
        # Will fail without API key, but tests code path
        result = await analyze_image_universal(
            base64_data=test_image_base64,
            mime_type="image/png",
            filename="test.png"
        )
        
        # Should return None or string
        assert result is None or isinstance(result, str)


class TestTTSProvider:
    """Test tts_elevenlabs.py"""
    
    def test_tts_imports(self):
        """Test TTS provider imports"""
        from tts_elevenlabs import text_to_speech, POLISH_VOICES
        assert callable(text_to_speech)
        assert "rachel" in POLISH_VOICES
    
    @pytest.mark.asyncio
    async def test_tts_voices_defined(self):
        """Test TTS voices are defined"""
        from tts_elevenlabs import POLISH_VOICES
        
        expected_voices = ["rachel", "antoni", "adam", "bella"]
        for voice in expected_voices:
            assert voice in POLISH_VOICES
    
    @pytest.mark.asyncio
    async def test_tts_generation(self):
        """Test TTS audio generation"""
        from tts_elevenlabs import text_to_speech
        
        # Will fail without API key, but tests code path
        result = await text_to_speech("Test")
        
        # Should return None or bytes
        assert result is None or isinstance(result, bytes)


class TestCaptchaSolver:
    """Test captcha_solver.py"""
    
    def test_captcha_imports(self):
        """Test captcha solver imports"""
        from captcha_solver import solve_recaptcha, solve_hcaptcha
        assert callable(solve_recaptcha)
        assert callable(solve_hcaptcha)
    
    @pytest.mark.asyncio
    async def test_recaptcha_solver(self):
        """Test reCAPTCHA solver"""
        from captcha_solver import solve_recaptcha
        
        # Will fail without API key, but tests code path
        result = await solve_recaptcha(
            site_key="test_key",
            page_url="https://example.com"
        )
        
        # Should return None or string token
        assert result is None or isinstance(result, str)


class TestProactiveSuggestions:
    """Test proactive_suggestions.py"""
    
    def test_suggestions_imports(self):
        """Test proactive suggestions imports"""
        from proactive_suggestions import get_smart_suggestions as generate_suggestions
        assert callable(generate_suggestions)
    
    @pytest.mark.asyncio
    async def test_suggestions_generation(self):
        """Test suggestions generation"""
        from proactive_suggestions import get_smart_suggestions
        
        suggestions = get_smart_suggestions("Opowiedz o Krakowie", "Kraków to piękne miasto...")
        
        # Should return list
        assert isinstance(suggestions, list)


class TestAdvancedProactiveSuggestions:
    """Test advanced_proactive.py - Zaawansowany system proaktywnych sugestii"""
    
    def test_advanced_suggestions_imports(self):
        """Test advanced proactive suggestions imports"""
        # Jeśli importy działają, to znaczy, że moduł jest poprawnie zainstalowany
        from advanced_proactive import (
            get_proactive_suggestions, 
            inject_suggestions_to_prompt,
            suggestion_generator
        )
        assert callable(get_proactive_suggestions)
        assert callable(inject_suggestions_to_prompt)
        assert hasattr(suggestion_generator, 'conversation_analyzer')
        assert hasattr(suggestion_generator, 'generate_suggestions')
    
    @pytest.mark.asyncio
    async def test_conversation_analyzer(self):
        """Test analizatora konwersacji"""
        from advanced_proactive import suggestion_generator
        
        # Test analizy wiadomości
        analysis = suggestion_generator.conversation_analyzer.analyze_message(
            user_id="test_user",
            message="Mam problem z kodem Python, wyskakuje błąd ImportError"
        )
        
        # Sprawdź czy analiza zwraca oczekiwane pola
        assert isinstance(analysis, dict)
        assert "main_topic" in analysis
        assert "topics" in analysis
        assert "main_intent" in analysis
        assert "intents" in analysis
        assert "is_focused" in analysis
        
        # Sprawdź czy analiza wykryła temat programistyczny
        assert analysis["main_topic"] == "programming" or any("programming" == t[0] for t in analysis["topics"])
    
    @pytest.mark.asyncio
    async def test_proactive_suggestion_generation(self):
        """Test generowania proaktywnych sugestii"""
        from advanced_proactive import get_proactive_suggestions
        
        # Przygotuj dane testowe
        user_id = "test_user"
        message = "Szukam dobrego hotelu w Warszawie na weekend"
        conversation_history = [
            {"role": "user", "content": "Planuję wyjazd do Warszawy"},
            {"role": "assistant", "content": "Warszawa to świetny wybór! Co chciałbyś wiedzieć?"}
        ]
        
        # Wygeneruj sugestie
        suggestions = await get_proactive_suggestions(
            user_id=user_id,
            message=message,
            conversation_history=conversation_history,
            force=True  # Wymuszamy sugestie mimo cooldown
        )
        
        # Sprawdź czy sugestie są generowane poprawnie
        assert isinstance(suggestions, list)
        # Nieważne czy lista jest pusta czy nie, główne, że funkcja działa
        
        # Jeśli są jakieś sugestie, sprawdź ich strukturę
        if suggestions:
            assert "text" in suggestions[0]
            assert "score" in suggestions[0]
            assert "context" in suggestions[0]
    
    @pytest.mark.asyncio
    async def test_prompt_injection(self):
        """Test injekcji sugestii do promptu"""
        from advanced_proactive import inject_suggestions_to_prompt
        
        # Przygotuj dane testowe
        base_prompt = "Jesteś pomocnym asystentem AI."
        suggestions = [
            {
                "text": "💡 Mogę znaleźć najlepsze hotele w tej lokalizacji",
                "score": 0.9,
                "context": {"template_type": "standard"}
            }
        ]
        
        # Wstaw sugestie do promptu
        enhanced_prompt = inject_suggestions_to_prompt(base_prompt, suggestions)
        
        # Sprawdź czy prompt został poprawnie zmodyfikowany
        assert isinstance(enhanced_prompt, str)
        assert len(enhanced_prompt) > len(base_prompt)
        assert "💡 Mogę znaleźć najlepsze hotele" in enhanced_prompt
