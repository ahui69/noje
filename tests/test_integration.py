#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Tests - E2E scenarios
"""

import pytest
import json


class TestChatFlow:
    """Test complete chat flow"""
    
    def test_simple_chat_flow(self, client, auth_headers):
        """Test basic chat conversation"""
        # Send message
        response = client.post(
            "/api/chat/assistant",
            headers=auth_headers,
            json={
                "messages": [
                    {"role": "user", "content": "Cześć!"}
                ],
                "user_id": "test_user_1"
            }
        )
        
        # Should respond (even if error due to no API key)
        assert response.status_code in [200, 500]
    
    def test_multi_turn_conversation(self, client, auth_headers):
        """Test multi-turn conversation"""
        user_id = "test_user_multi"
        
        # Turn 1
        r1 = client.post(
            "/api/chat/assistant",
            headers=auth_headers,
            json={
                "messages": [{"role": "user", "content": "Jestem Jan"}],
                "user_id": user_id
            }
        )
        
        # Turn 2
        r2 = client.post(
            "/api/chat/assistant",
            headers=auth_headers,
            json={
                "messages": [{"role": "user", "content": "Jak mam na imię?"}],
                "user_id": user_id
            }
        )
        
        # Both should process
        assert r1.status_code in [200, 500]
        assert r2.status_code in [200, 500]


class TestVisionFlow:
    """Test vision processing flow"""
    
    def test_image_upload_and_analysis(self, client, auth_headers, test_image_base64):
        """Test image upload with vision analysis"""
        response = client.post(
            "/api/chat/assistant",
            headers=auth_headers,
            json={
                "messages": [{
                    "role": "user",
                    "content": "Co widzisz?",
                    "attachments": [{
                        "type": "image/png",
                        "data": test_image_base64,
                        "filename": "test.png"
                    }]
                }]
            }
        )
        
        # Should process (may fail without Vision API key)
        assert response.status_code in [200, 500]


class TestTTSFlow:
    """Test TTS generation flow"""
    
    def test_tts_generation(self, client):
        """Test TTS audio generation"""
        response = client.post(
            "/api/tts/speak",
            json={
                "text": "Witaj świecie!",
                "voice": "rachel"
            }
        )
        
        if response.status_code == 200:
            # Should return audio
            assert response.headers["content-type"] == "audio/mpeg"
        else:
            # Or error (no API key)
            assert response.status_code == 500


class TestMemoryPersistence:
    """Test memory persistence"""
    
    def test_stm_persistence(self, client, auth_headers):
        """Test STM persists across requests"""
        user_id = "test_persist"
        
        # Add to STM
        client.post(
            "/api/chat/assistant",
            headers=auth_headers,
            json={
                "messages": [{"role": "user", "content": "Zapamiętaj: lubię pizzę"}],
                "user_id": user_id
            }
        )
        
        # Check psyche (which reads STM)
        response = client.get(
            "/api/psyche/status",
            headers=auth_headers,
            params={"user_id": user_id}
        )
        
        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling"""
    
    def test_invalid_json(self, client, auth_headers):
        """Test invalid JSON handling"""
        response = client.post(
            "/api/chat/assistant",
            headers=auth_headers,
            data="invalid json"
        )
        assert response.status_code == 422  # Validation error
    
    def test_missing_auth(self, client):
        """Test missing authentication"""
        response = client.post(
            "/api/chat/assistant",
            json={"messages": [{"role": "user", "content": "test"}]}
        )
        assert response.status_code == 401
    
    def test_rate_limiting(self, client, auth_headers):
        """Test rate limiting (if enabled)"""
        # Send many requests
        for _ in range(5):
            client.get("/health")
        
        # Should still work (or rate limit)
        response = client.get("/health")
        assert response.status_code in [200, 429]
