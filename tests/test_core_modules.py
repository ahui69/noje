#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core Modules Tests
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestConfig:
    """Test core/config.py"""
    
    def test_config_loads(self):
        """Test config module loads"""
        from core import config
        assert hasattr(config, 'LLM_BASE_URL')
    
    def test_env_defaults(self):
        """Test environment defaults"""
        from core import config
        # Should have defaults even without .env
        assert config.AUTH_TOKEN is not None


class TestAuth:
    """Test core/auth.py"""
    
    def test_auth_imports(self):
        """Test auth module imports"""
        from core import auth
        assert hasattr(auth, 'check_auth')

    def test_auth_verify(self):
        """Test token verification"""
        from core.auth import check_auth
        from fastapi import Request
        from unittest.mock import Mock

        # Mock request with valid token
        mock_request = Mock(spec=Request)
        mock_request.headers = {"authorization": "Bearer ssjjMijaja6969"}

        # Valid token
        assert check_auth(mock_request) is True

        # Mock request with invalid token
        mock_request.headers = {"authorization": "Bearer wrong"}
        assert check_auth(mock_request) is False


class TestHelpers:
    """Test core/helpers.py"""
    
    def test_helpers_imports(self):
        """Test helpers module"""
        from core import helpers
        assert hasattr(helpers, 'log_info') or hasattr(helpers, 'log_error')


class TestMemory:
    """Test core/memory.py"""
    
    def test_memory_imports(self):
        """Test memory module"""
        from core import memory
        assert hasattr(memory, 'stm_get_context') or hasattr(memory, 'stm_add')
    
    def test_stm_operations(self):
        """Test STM operations"""
        from core.memory import stm_add, stm_get_context
        
        # Add to STM
        stm_add(role="user", content="Test message", user="test_user")
        
        # Retrieve STM
        messages = stm_get_context(user="test_user")
        assert len(messages) > 0


class TestLLM:
    """Test core/llm.py"""
    
    def test_llm_imports(self):
        """Test LLM module"""
        from core import llm
        assert hasattr(llm, 'LLM_BASE_URL') or hasattr(llm, 'LLM_API_KEY')


class TestSemantic:
    """Test core/semantic.py"""
    
    def test_semantic_imports(self):
        """Test semantic module"""
        from core import semantic
        assert hasattr(semantic, 'SemanticAnalyzer')


class TestResearch:
    """Test core/research.py"""
    
    def test_research_imports(self):
        """Test research module"""
        from core import research
        assert hasattr(research, 'chunk_text')


class TestTools:
    """Test core/tools.py"""
    
    def test_tools_imports(self):
        """Test tools module"""
        from core import tools
        # Check for any tool functions
        assert dir(tools)  # Has some exports


class TestWriting:
    """Test core/writing.py"""
    
    def test_writing_imports(self):
        """Test writing module"""
        from core import writing
        # Check module exists
        assert dir(writing)
