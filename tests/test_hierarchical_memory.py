#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the Hierarchical Memory System.
"""

import pytest
import os
import sys
import time
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.hierarchical_memory import (
    EpisodicMemoryManager,
    SemanticMemoryManager,
    ProceduralMemoryManager,
    HierarchicalMemory,
    hierarchical_memory_manager
)
from core.memory import _db, ltm_add, ltm_search_hybrid

# Fixture to ensure a clean database for each test class
@pytest.fixture(scope="class")
def clean_db():
    """Provides a clean database for the test class."""
    db_path = os.getenv("MEM_DB", "test_hierarchical_mem.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Set env for the db used by the modules
    os.environ["MEM_DB"] = db_path
    
    # Re-initialize the database schema
    from core.memory import _init_db as init_main_db
    init_main_db()
    
    # The hierarchical memory initializes its own tables
    # We can create a dummy instance to ensure tables are created
    HierarchicalMemory()
    
    yield
    
    # Clean up the test database
    if os.path.exists(db_path):
        os.remove(db_path)

@pytest.mark.usefixtures("clean_db")
class TestEpisodicMemory:
    """Tests for the EpisodicMemoryManager (L1)."""

    def test_record_and_retrieve_episode(self):
        """Test recording and retrieving a single episode."""
        manager = EpisodicMemoryManager()
        user_id = "test_user_L1"
        summary = "User asked about the weather in Warsaw."
        metadata = {"city": "Warsaw", "question": "weather"}
        
        episode_id = manager.record_episode(user_id, "conversation_turn", summary, metadata=metadata)
        assert isinstance(episode_id, str)

        related_episodes = manager.find_related_episodes("weather Warsaw", user_id)
        assert len(related_episodes) == 1
        episode = related_episodes[0]
        assert episode['summary'] == summary
        assert json.loads(episode['metadata'])['city'] == "Warsaw"

@pytest.mark.usefixtures("clean_db")
class TestSemanticMemory:
    """Tests for the SemanticMemoryManager (L2)."""

    def test_fact_consolidation(self):
        """Test consolidating a semantic fact from multiple episodes."""
        episodic_manager = EpisodicMemoryManager()
        semantic_manager = SemanticMemoryManager()
        user_id = "test_user_L2"

        # Record several related episodes
        episodes_data = [
            {"summary": "User wants to book a flight to New York."},
            {"summary": "User is asking about hotels in New York."},
            {"summary": "User is looking for tourist attractions in New York."},
            {"summary": "User mentioned they love visiting New York."},
            {"summary": "User confirmed their travel plans to New York."}
        ]
        
        recorded_episodes = []
        for data in episodes_data:
            episodic_manager.record_episode(user_id, "conversation_turn", data['summary'])
            # We need to retrieve them to have the full dict structure for consolidation
            time.sleep(0.01) # ensure unique timestamps
            recorded_episodes.extend(episodic_manager.find_related_episodes(data['summary'], user_id, limit=1))

        # Consolidate a fact
        fact_id = semantic_manager.consolidate_fact_from_episodes(recorded_episodes, user_id)
        assert fact_id is not None
        
        # Verify the fact was added to LTM
        search_results = ltm_search_hybrid("user New York", limit=5)
        assert len(search_results) > 0
        consolidated_fact_found = any("Na podstawie kilku interakcji" in r['text'] for r in search_results)
        assert consolidated_fact_found

@pytest.mark.usefixtures("clean_db")
class TestProceduralMemory:
    """Tests for the ProceduralMemoryManager (L3)."""

    def test_procedure_learning_and_retrieval(self):
        """Test learning a procedure and retrieving it after enough successful executions."""
        manager = ProceduralMemoryManager()
        intent = "find_cheapest_flight"
        steps = ["search_flights(destination, date)", "sort_by_price()", "select_top_result()"]

        # First execution - procedure is created but not yet "learned"
        manager.learn_or_update_procedure(intent, steps)
        procedure = manager.get_procedure(intent)
        assert procedure is None  # Not learned yet (threshold not met)

        # Subsequent executions
        for _ in range(4): # Assuming threshold is 3, we need 2 more + 2 for good measure
            manager.learn_or_update_procedure(intent, steps)

        # Now the procedure should be learned
        procedure = manager.get_procedure(intent)
        assert procedure is not None
        assert isinstance(procedure, list)
        assert procedure == steps

@pytest.mark_usefixtures("clean_db")
class TestHierarchicalMemoryIntegration:
    """Tests the integrated HierarchicalMemory class."""

    def test_full_conversation_turn_processing(self):
        """Test the full pipeline of processing a conversation turn."""
        user_id = "test_user_integrated"
        user_msg = "I want to book a flight to Berlin for next week."
        assistant_resp = "Sure, I can help with that. What are the exact dates?"
        intent = "book_flight"
        actions = ["identify_intent('book_flight')", "ask_for_dates()"]

        # Process the turn
        hierarchical_memory_manager.process_conversation_turn(
            user_id=user_id,
            user_message=user_msg,
            assistant_response=assistant_resp,
            stm_ids=["stm_id_1", "stm_id_2"],
            intent=intent,
            executed_actions=actions
        )

        # Check L1 - Episodic Memory
        episodes = hierarchical_memory_manager.episodic.find_related_episodes("flight to Berlin", user_id)
        assert len(episodes) > 0
        assert "User: 'I want to book a flight" in episodes[0]['summary']

        # Check L3 - Procedural Memory (it's been executed once)
        procedure = hierarchical_memory_manager.procedural.get_procedure(intent)
        assert procedure is None # Not learned yet

        # Simulate more executions to learn the procedure
        for _ in range(3):
            hierarchical_memory_manager.procedural.learn_or_update_procedure(intent, actions)
        
        procedure = hierarchical_memory_manager.procedural.get_procedure(intent)
        assert procedure == actions

    def test_get_context_for_query(self):
        """Test retrieving context from all memory levels."""
        user_id = "test_user_context"
        query = "I need to find a hotel in Paris."

        # Seed memory with some data
        hierarchical_memory_manager.episodic.record_episode(user_id, "observation", "User previously searched for museums in Paris.")
        ltm_add("Paris is the capital of France.", tags=f"user:{user_id},semantic", conf=0.9)
        
        # Get context
        context = hierarchical_memory_manager.get_context_for_query(user_id, query)

        assert "L1_episodes" in context
        assert "L2_semantic_facts" in context
        assert "L3_procedure" in context

        assert len(context['L1_episodes']) > 0
        assert "museums in Paris" in context['L1_episodes'][0]['summary']

        assert len(context['L2_semantic_facts']) > 0
        assert "capital of France" in context['L2_semantic_facts'][0]['text']
