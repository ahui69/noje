#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pytest configuration and fixtures
"""

import pytest
import os
import sys
from fastapi.testclient import TestClient

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

@pytest.fixture
def client():
    """FastAPI test client"""
    from app import app
    return TestClient(app)

@pytest.fixture
def auth_headers():
    """Authentication headers"""
    return {"Authorization": "Bearer ssjjMijaja6969"}

@pytest.fixture
def test_message():
    """Sample message for testing"""
    return {
        "messages": [
            {"role": "user", "content": "Cześć, jak się masz?"}
        ]
    }

@pytest.fixture
def test_image_base64():
    """Sample base64 image for testing"""
    # 1x1 pixel PNG
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
