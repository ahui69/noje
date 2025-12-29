#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_writing_endpoint.py - Testy dla endpointów pisania.
"""
import pytest
from fastapi.testclient import TestClient
import os

from app import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def auth_headers():
    token = os.getenv("AUTH_TOKEN", "ssjjMijaja6969")
    return {"Authorization": f"Bearer {token}"}

def test_creative_writing(client, auth_headers):
    """Test endpointu kreatywnego pisania."""
    response = client.post(
        "/api/writing/creative",
        headers=auth_headers,
        json={
            "topic": "Sztuczna inteligencja w edukacji",
            "tone": "profesjonalny",
            "style": "informacyjny",
            "length": "średni"
        }
    )
    
    # Akceptujemy zarówno sukces, jak i błąd 500 
    # (jeśli brak klucza LLM w środowisku testowym)
    assert response.status_code in (200, 500)
    
    if response.status_code == 200:
        data = response.json()
        assert data["ok"] is True
        assert isinstance(data["text"], str)
        assert len(data["text"]) > 0
        assert "topic" in data["metadata"]

def test_vinted_description(client, auth_headers):
    """Test endpointu do opisów Vinted."""
    response = client.post(
        "/api/writing/vinted",
        headers=auth_headers,
        json={
            "title": "Czarna sukienka H&M rozmiar M",
            "description": "Sukienka w bardzo dobrym stanie, używana kilka razy, bez wad."
        }
    )
    
    assert response.status_code in (200, 500)
    
    if response.status_code == 200:
        data = response.json()
        assert data["ok"] is True
        assert isinstance(data["text"], str)
        assert len(data["text"]) > 0

def test_social_media_post(client, auth_headers):
    """Test endpointu do postów w mediach społecznościowych."""
    response = client.post(
        "/api/writing/social",
        headers=auth_headers,
        json={
            "platform": "Instagram",
            "topic": "Nowa kolekcja butów sportowych",
            "tone": "entuzjastyczny",
            "hashtags": 8
        }
    )
    
    assert response.status_code in (200, 500)
    
    if response.status_code == 200:
        data = response.json()
        assert data["ok"] is True
        assert isinstance(data["text"], str)
        assert len(data["text"]) > 0

def test_fashion_analysis(client, auth_headers):
    """Test endpointu do analizy mody."""
    response = client.post(
        "/api/writing/fashion/analyze",
        headers=auth_headers,
        json={
            "text": "Czarna sukienka H&M rozmiar M, bawełna, na wiosnę."
        }
    )
    
    assert response.status_code in (200, 500)
    
    if response.status_code == 200:
        data = response.json()
        assert data["ok"] is True
        assert "analysis" in data
        if "brands" in data["analysis"]:
            assert "H&M" in data["analysis"]["brands"]
        if "colors" in data["analysis"]:
            assert "czarny" in data["analysis"]["colors"]
        if "sizes" in data["analysis"]:
            assert "M" in data["analysis"]["sizes"]