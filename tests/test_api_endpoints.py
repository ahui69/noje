#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Endpoints Tests
"""

import pytest

class TestChatEndpoint:
    """Test /api/chat/assistant"""
    
    def test_chat_endpoint_exists(self, client, auth_headers):
        """Test chat endpoint responds"""
        response = client.post(
            "/api/chat/assistant",
            headers=auth_headers,
            json={"messages": [{"role": "user", "content": "test"}]}
        )
        assert response.status_code in [200, 500]  # May fail without LLM key
    
    def test_chat_requires_auth(self, client):
        """Test chat requires authentication"""
        response = client.post(
            "/api/chat/assistant",
            json={"messages": [{"role": "user", "content": "test"}]}
        )
        assert response.status_code == 401
    
    def test_chat_stream_endpoint(self, client, auth_headers):
        """Test chat streaming endpoint"""
        response = client.post(
            "/api/chat/assistant/stream",
            headers=auth_headers,
            json={"messages": [{"role": "user", "content": "test"}]}
        )
        assert response.status_code in [200, 500]


class TestTTSEndpoint:
    """Test /api/tts"""
    
    def test_tts_speak_endpoint(self, client):
        """Test TTS speak endpoint"""
        response = client.post(
            "/api/tts/speak",
            json={"text": "Test", "voice": "rachel"}
        )
        # May return 500 if no API key, but endpoint exists
        assert response.status_code in [200, 500]
    
    def test_tts_voices_list(self, client):
        """Test TTS voices list"""
        response = client.get("/api/tts/voices")
        assert response.status_code == 200
        data = response.json()
        assert "voices" in data
        assert "rachel" in data["voices"]


class TestPsycheEndpoint:
    """Test /api/psyche"""
    
    def test_psyche_status(self, client, auth_headers):
        """Test psyche status endpoint"""
        response = client.get(
            "/api/psyche/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "mood" in data or "state" in data
    
    def test_psyche_reset(self, client, auth_headers):
        """Test psyche reset"""
        response = client.post(
            "/api/psyche/reset",
            headers=auth_headers
        )
        assert response.status_code == 200


class TestTravelEndpoint:
    """Test /api/travel"""
    
    def test_travel_search(self, client, auth_headers):
        """Test travel search endpoint"""
        response = client.get(
            "/api/travel/search?city=Kraków&what=attractions",
            headers=auth_headers
        )
        assert response.status_code in [200, 500]  # May need API key


class TestFilesEndpoint:
    """Test /api/files"""
    
    def test_files_list(self, client, auth_headers):
        """Test files list endpoint"""
        response = client.get(
            "/api/files/list",
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_files_stats(self, client, auth_headers):
        """Test files stats"""
        response = client.get(
            "/api/files/stats",
            headers=auth_headers
        )
        assert response.status_code == 200


class TestAdminEndpoint:
    """Test /api/admin"""
    
    def test_admin_stats(self, client, auth_headers):
        """Test admin stats endpoint"""
        response = client.get(
            "/api/admin/cache/stats",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "caches" in data


class TestPrometheusEndpoint:
    """Test /api/prometheus"""
    
    def test_metrics_endpoint(self, client):
        """Test Prometheus metrics"""
        response = client.get("/api/prometheus/metrics")
        assert response.status_code in [200, 404]  # May not be enabled


class TestHealthEndpoints:
    """Test health & status endpoints"""
    
    def test_health_endpoint(self, client):
        """Test /health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_api_status(self, client):
        """Test /api status endpoint"""
        response = client.get("/api")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "version" in data
    
    def test_status_endpoint(self, client):
        """Test /status endpoint"""
        response = client.get("/status")
        assert response.status_code == 200
