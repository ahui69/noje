# 01 ZAŁĄCZNIK: PEŁNA LISTA PLIKÓW .PY (LINUX)

**Data:** 26 grudnia 2025  
**Środowisko:** Linux (bash)  
**Katalog roboczy:** `mrd/`

---

## KOMENDY UŻYTE DO WYGENEROWANIA

```bash
# Pełna lista posortowana:
find . -type f -name "*.py" -print | sort

# Licznik:
find . -type f -name "*.py" -print | wc -l

# Podział per katalog:
find . -type f -name "*.py" -printf '%h\n' | sort | uniq -c | sort -nr
```

---

## PODSUMOWANIE

| Katalog     | Ilość plików |
| ----------- | ------------ |
| `.` (root)  | 65           |
| `./core`    | 67           |
| `./tests`   | 10           |
| `./tools`   | 2            |
| `./scripts` | 1            |
| **RAZEM**   | **145**      |

---

## PEŁNA LISTA (145 PLIKÓW)

```
./app.py
./assistant_endpoint.py
./assistant_simple.py
./audit_adv_cog_extract.py
./autonauka_pro.py
./core/__init__.py
./core/admin_endpoint.py
./core/advanced_autorouter.py
./core/advanced_cognitive_engine.py
./core/advanced_learning.py
./core/advanced_llm.py
./core/advanced_memory.py
./core/advanced_proactive.py
./core/advanced_psychology.py
./core/ai_auction.py
./core/app.py
./core/assistant_endpoint.py
./core/auction_endpoint.py
./core/auth.py
./core/autoroute.py
./core/batch_endpoint.py
./core/batch_processing.py
./core/brave_search.py
./core/chat_advanced_endpoint.py
./core/cognitive_endpoint.py
./core/cognitive_engine.py
./core/config.py
./core/context_awareness.py
./core/conversation_analytics.py
./core/executor.py
./core/fact_validation.py
./core/future_predictor.py
./core/hacker_endpoint.py
./core/helpers.py
./core/hierarchical_memory.py
./core/hybrid_search_endpoint.py
./core/inner_language.py
./core/intent_dispatcher.py
./core/knowledge_compression.py
./core/legal_office_endpoint.py
./core/llm.py
./core/memory.py
./core/memory_endpoint.py
./core/memory_persistence.py
./core/memory_store.py
./core/memory_summarizer.py
./core/metrics.py
./core/middleware.py
./core/multi_agent_orchestrator.py
./core/negocjator_endpoint.py
./core/nlp_processor.py
./core/parallel.py
./core/prometheus_endpoint.py
./core/prompt.py
./core/psyche_endpoint.py
./core/redis_middleware.py
./core/reflection_endpoint.py
./core/research.py
./core/research_endpoint.py
./core/response_adapter.py
./core/self_reflection.py
./core/semantic.py
./core/sessions.py
./core/smart_context.py
./core/stress_test_system.py
./core/suggestions_endpoint.py
./core/tavily_search.py
./core/tools.py
./core/tools_registry.py
./core/ultra_destruction_test.py
./core/user_model.py
./core/writing.py
./deploy.py
./example.py
./files_endpoint.py
./fix_conversations_tables.py
./fix_hier_mem_await.py
./fix_openai_compat_boundary_hard.py
./fix_openai_compat_broken_strings.py
./hierarchical_memory.py
./hybrid_search_endpoint.py
./internal_endpoint.py
./nlp_endpoint.py
./openai_compat.py
./patch_add_cognitive_mode_enum.py
./patch_add_get_advanced_cognitive_engine.py
./patch_app_nonfatal_failed_routers.py
./patch_bootstrap_advanced_cognitive_types.py
./patch_chatbox_buffer.py
./patch_disable_any_router_exception_handler_router_vars.py
./patch_disable_apirouter_exception_handler_repo_wide.py
./patch_fix_deploy_py_fstring_backslash.py
./patch_fix_future_import_position_in_advanced_cognitive_engine.py
./patch_fix_writing_fstring_resub_cat_tag.py
./patch_fix_writing_hashtags_fstring_regex.py
./patch_force_alias_get_advanced_cognitive_engine.py
./patch_move_cognitive_mode_to_top.py
./patch_mrd_fix_compile_and_failed_routers.py
./patch_mrd_fix_fstrings_and_router_exception_handler.py
./patch_nonfatal_failed_routers_everywhere.py
./patch_stream_finaldelta.py
./patch_stream_pingflush.py
./print_routes.py
./proactive_suggestions.py
./programista_endpoint.py
./prometheus_endpoint.py
./psyche_endpoint.py
./research.py
./research_endpoint.py
./routers.py
./scripts/check_requirements.py
./set_memory_db_env.py
./sports_news_pro.py
./stress_test_system.py
./stt_endpoint.py
./suggestions_endpoint.py
./system_stats.py
./test_web_learn.py
./tests/__init__.py
./tests/conftest.py
./tests/test_api_endpoints.py
./tests/test_batch_processing.py
./tests/test_core_modules.py
./tests/test_hierarchical_memory.py
./tests/test_integration.py
./tests/test_proactive_suggestions.py
./tests/test_vision_tts.py
./tests/test_writing_endpoint.py
./tools/mrd_repo_index.py
./tools/patch_hybrid_pick.py
./tools_fix_hybrid_primary.py
./tools_fix_hybrid_primary_v2.py
./tools_fix_hybrid_router.py
./tools_patch_app_aliases.py
./tools_patch_app_get_automation_summary.py
./tools_patch_app_get_automation_summary_refresh.py
./tools_patch_hybrid_call_helper.py
./tools_patch_hybrid_callsite.py
./travel_endpoint.py
./tts_elevenlabs.py
./tts_endpoint.py
./ultra_destruction_test.py
./vision_provider.py
./writer_pro.py
./writing_endpoint.py
```

---

## ROZBICIE NA KATALOGI

### ROOT `.` (65 plików)

```
./app.py
./assistant_endpoint.py
./assistant_simple.py
./audit_adv_cog_extract.py
./autonauka_pro.py
./deploy.py
./example.py
./files_endpoint.py
./fix_conversations_tables.py
./fix_hier_mem_await.py
./fix_openai_compat_boundary_hard.py
./fix_openai_compat_broken_strings.py
./hierarchical_memory.py
./hybrid_search_endpoint.py
./internal_endpoint.py
./nlp_endpoint.py
./openai_compat.py
./patch_add_cognitive_mode_enum.py
./patch_add_get_advanced_cognitive_engine.py
./patch_app_nonfatal_failed_routers.py
./patch_bootstrap_advanced_cognitive_types.py
./patch_chatbox_buffer.py
./patch_disable_any_router_exception_handler_router_vars.py
./patch_disable_apirouter_exception_handler_repo_wide.py
./patch_fix_deploy_py_fstring_backslash.py
./patch_fix_future_import_position_in_advanced_cognitive_engine.py
./patch_fix_writing_fstring_resub_cat_tag.py
./patch_fix_writing_hashtags_fstring_regex.py
./patch_force_alias_get_advanced_cognitive_engine.py
./patch_move_cognitive_mode_to_top.py
./patch_mrd_fix_compile_and_failed_routers.py
./patch_mrd_fix_fstrings_and_router_exception_handler.py
./patch_nonfatal_failed_routers_everywhere.py
./patch_stream_finaldelta.py
./patch_stream_pingflush.py
./print_routes.py
./proactive_suggestions.py
./programista_endpoint.py
./prometheus_endpoint.py
./psyche_endpoint.py
./research.py
./research_endpoint.py
./routers.py
./set_memory_db_env.py
./sports_news_pro.py
./stress_test_system.py
./stt_endpoint.py
./suggestions_endpoint.py
./system_stats.py
./test_web_learn.py
./tools_fix_hybrid_primary.py
./tools_fix_hybrid_primary_v2.py
./tools_fix_hybrid_router.py
./tools_patch_app_aliases.py
./tools_patch_app_get_automation_summary.py
./tools_patch_app_get_automation_summary_refresh.py
./tools_patch_hybrid_call_helper.py
./tools_patch_hybrid_callsite.py
./travel_endpoint.py
./tts_elevenlabs.py
./tts_endpoint.py
./ultra_destruction_test.py
./vision_provider.py
./writer_pro.py
./writing_endpoint.py
```

### CORE `./core` (67 plików)

```
./core/__init__.py
./core/admin_endpoint.py
./core/advanced_autorouter.py
./core/advanced_cognitive_engine.py
./core/advanced_learning.py
./core/advanced_llm.py
./core/advanced_memory.py
./core/advanced_proactive.py
./core/advanced_psychology.py
./core/ai_auction.py
./core/app.py
./core/assistant_endpoint.py
./core/auction_endpoint.py
./core/auth.py
./core/autoroute.py
./core/batch_endpoint.py
./core/batch_processing.py
./core/brave_search.py
./core/chat_advanced_endpoint.py
./core/cognitive_endpoint.py
./core/cognitive_engine.py
./core/config.py
./core/context_awareness.py
./core/conversation_analytics.py
./core/executor.py
./core/fact_validation.py
./core/future_predictor.py
./core/hacker_endpoint.py
./core/helpers.py
./core/hierarchical_memory.py
./core/hybrid_search_endpoint.py
./core/inner_language.py
./core/intent_dispatcher.py
./core/knowledge_compression.py
./core/legal_office_endpoint.py
./core/llm.py
./core/memory.py
./core/memory_endpoint.py
./core/memory_persistence.py
./core/memory_store.py
./core/memory_summarizer.py
./core/metrics.py
./core/middleware.py
./core/multi_agent_orchestrator.py
./core/negocjator_endpoint.py
./core/nlp_processor.py
./core/parallel.py
./core/prometheus_endpoint.py
./core/prompt.py
./core/psyche_endpoint.py
./core/redis_middleware.py
./core/reflection_endpoint.py
./core/research.py
./core/research_endpoint.py
./core/response_adapter.py
./core/self_reflection.py
./core/semantic.py
./core/sessions.py
./core/smart_context.py
./core/stress_test_system.py
./core/suggestions_endpoint.py
./core/tavily_search.py
./core/tools.py
./core/tools_registry.py
./core/ultra_destruction_test.py
./core/user_model.py
./core/writing.py
```

### TESTS `./tests` (10 plików)

```
./tests/__init__.py
./tests/conftest.py
./tests/test_api_endpoints.py
./tests/test_batch_processing.py
./tests/test_core_modules.py
./tests/test_hierarchical_memory.py
./tests/test_integration.py
./tests/test_proactive_suggestions.py
./tests/test_vision_tts.py
./tests/test_writing_endpoint.py
```

### TOOLS `./tools` (2 pliki)

```
./tools/mrd_repo_index.py
./tools/patch_hybrid_pick.py
```

### SCRIPTS `./scripts` (1 plik)

```
./scripts/check_requirements.py
```
