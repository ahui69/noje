# 01. MAPA PROJEKTU + ENTRYPOINT TRUTH

**Data audytu:** 26 grudnia 2025  
**Zakres:** Wszystkie 145 plików `.py` w `mrd/**` (rekurencyjnie)  
**Załącznik:** [01_FILES_FULL_LIST.md](01_FILES_FULL_LIST.md) — pełna lista

---

## 0. ŚRODOWISKO AUDYTU

| Parametr                            | Wartość                                                 |
| ----------------------------------- | ------------------------------------------------------- |
| **System**                          | Linux (bash)                                            |
| **Katalog roboczy**                 | `mrd/`                                                  |
| **Repozytorium**                    | brak git (katalog lokalny)                              |
| **Metoda generowania listy plików** | `find . -type f -name "*.py" -print \| sort`            |
| **Licznik plików**                  | `find . -type f -name "*.py" -print \| wc -l` → **145** |

**UWAGA:** Wszystkie ścieżki w audycie używają formatu Linux (`./core/app.py`), nie Windows.

---

## 1. STRUKTURA KATALOGÓW

```
mrd/                                    # ROOT - 65 plików .py
├── app.py                              # ⭐ ENTRYPOINT #1 (produkcyjny)
├── core/                               # CORE MODULES - 67 plików .py
│   ├── __init__.py
│   ├── app.py                          # ⚠️ ENTRYPOINT #2 (alternatywny, NIE UŻYWAĆ z root)
│   ├── config.py                       # Konfiguracja centralna
│   ├── auth.py                         # Autoryzacja
│   ├── llm.py                          # LLM client
│   ├── memory.py                       # Unified Memory System (2400+ linii)
│   ├── cognitive_engine.py             # Główny orchestrator AI
│   └── ...                             # (61 więcej modułów)
├── tests/                              # TESTY - 10 plików
│   ├── __init__.py
│   ├── conftest.py
│   └── test_*.py                       # 8 plików testowych
├── tools/                              # NARZĘDZIA DEV - 2 pliki
│   ├── mrd_repo_index.py
│   └── patch_hybrid_pick.py
├── scripts/                            # SKRYPTY - 1 plik
│   └── check_requirements.py
├── data/                               # DANE (bez .py)
├── logs/                               # LOGI (bez .py)
├── ltm_storage/                        # STORAGE (bez .py)
└── static/                             # FRONTEND ASSETS
```

---

## 2. PEŁNA LISTA PLIKÓW .PY (145 PLIKÓW)

### 2.1. ROOT `mrd/` (89 plików)

#### ENTRYPOINTY I APLIKACJE FASTAPI

| #   | Plik                                           | Linie | Typ               | Opis                                                     |
| --- | ---------------------------------------------- | ----- | ----------------- | -------------------------------------------------------- |
| 1   | [app.py](app.py)                               | 293   | **ENTRYPOINT #1** | Główna aplikacja FastAPI, ładuje 16 routerów dynamicznie |
| 2   | [openai_compat.py](openai_compat.py)           | ~400  | Router            | OpenAI-compatible `/v1/*` endpoints                      |
| 3   | [assistant_simple.py](assistant_simple.py)     | ~300  | Router            | Prosty chat `/api/chat/assistant`                        |
| 4   | [assistant_endpoint.py](assistant_endpoint.py) | ~200  | Router            | Alternatywny chat endpoint (konflikt z assistant_simple) |

#### ENDPOINTY (ROUTERY FASTAPI)

| #   | Plik                                                   | Router prefix      | Ładowany przez                         |
| --- | ------------------------------------------------------ | ------------------ | -------------------------------------- |
| 5   | [stt_endpoint.py](stt_endpoint.py)                     | `/api/stt`         | app.py ✅                              |
| 6   | [tts_endpoint.py](tts_endpoint.py)                     | `/api/tts`         | app.py ✅                              |
| 7   | [suggestions_endpoint.py](suggestions_endpoint.py)     | `/api/suggestions` | app.py ✅                              |
| 8   | [internal_endpoint.py](internal_endpoint.py)           | `/api/internal`    | app.py ✅                              |
| 9   | [files_endpoint.py](files_endpoint.py)                 | `/api/files`       | app.py ✅                              |
| 10  | [routers.py](routers.py)                               | `/api/routers`     | app.py ✅                              |
| 11  | [writing_endpoint.py](writing_endpoint.py)             | `/api/writing`     | core/app.py ❌ NIE app.py              |
| 12  | [psyche_endpoint.py](psyche_endpoint.py)               | `/api/psyche`      | core/app.py ❌ NIE app.py              |
| 13  | [travel_endpoint.py](travel_endpoint.py)               | `/api/travel`      | core/app.py ❌ NIE app.py              |
| 14  | [research_endpoint.py](research_endpoint.py)           | `/api/research`    | core/app.py ❌ NIE app.py              |
| 15  | [programista_endpoint.py](programista_endpoint.py)     | `/api/code`        | core/app.py ❌ NIE app.py              |
| 16  | [prometheus_endpoint.py](prometheus_endpoint.py)       | brak (!)           | core/app.py z prefix `/api/prometheus` |
| 17  | [nlp_endpoint.py](nlp_endpoint.py)                     | `/api/nlp`         | ⚠️ NIEPODPIĘTY w app.py                |
| 18  | [hybrid_search_endpoint.py](hybrid_search_endpoint.py) | (re-export)        | re-eksportuje z core, nie samodzielny  |

#### MODUŁY BIZNESOWE (NIE ENDPOINTY)

| #   | Plik                                                 | Linie | Typ    | Importowany przez                                       |
| --- | ---------------------------------------------------- | ----- | ------ | ------------------------------------------------------- |
| 19  | [research.py](research.py)                           | ~200  | Moduł  | ⚠️ Duplikat core/ (wymaga pkt 07)                       |
| 20  | [hierarchical_memory.py](hierarchical_memory.py)     | ~100  | Moduł  | ⚠️ Duplikat core/ (wymaga pkt 07)                       |
| 21  | [proactive_suggestions.py](proactive_suggestions.py) | ~200  | Moduł  | suggestions_endpoint.py                                 |
| 22  | [system_stats.py](system_stats.py)                   | ~150  | Moduł  | routers.py                                              |
| 23  | [vision_provider.py](vision_provider.py)             | ~200  | Moduł  | files_endpoint.py, tts_endpoint.py                      |
| 24  | [tts_elevenlabs.py](tts_elevenlabs.py)               | ~150  | Moduł  | tts_endpoint.py                                         |
| 25  | [writer_pro.py](writer_pro.py)                       | ~300  | Router | ⚠️ NIEPODPIĘTY (definiuje `writer_router` nie `router`) |
| 26  | [autonauka_pro.py](autonauka_pro.py)                 | ~400  | Moduł  | ⚠️ NIEPODPIĘTY (wymaga pkt 07)                          |
| 27  | [sports_news_pro.py](sports_news_pro.py)             | ~300  | Moduł  | ⚠️ NIEPODPIĘTY (wymaga pkt 07)                          |

#### TESTY I PRZYKŁADY

| #   | Plik                                                   | Typ  | Opis                            |
| --- | ------------------------------------------------------ | ---- | ------------------------------- |
| 28  | [example.py](example.py)                               | Demo | Przykład użycia                 |
| 29  | [test_web_learn.py](test_web_learn.py)                 | Test | Test web learning               |
| 30  | [stress_test_system.py](stress_test_system.py)         | Test | Stress test (z `__main__`)      |
| 31  | [ultra_destruction_test.py](ultra_destruction_test.py) | Test | Destruction test (z `__main__`) |

#### NARZĘDZIA DEPLOYMENTU

| #   | Plik                                         | Typ    | Opis                                    |
| --- | -------------------------------------------- | ------ | --------------------------------------- |
| 32  | [deploy.py](deploy.py)                       | Deploy | Skrypt deploymentu (z `__main__`)       |
| 33  | [print_routes.py](print_routes.py)           | Util   | Wypisuje wszystkie trasy (z `__main__`) |
| 34  | [set_memory_db_env.py](set_memory_db_env.py) | Util   | Ustawia MEM_DB env (z `__main__`)       |

#### SKRYPTY PATCHOWE (35 PLIKÓW - JEDNORAZOWE)

| #   | Plik                                                                                                                                 | Cel patcha                            |
| --- | ------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------- |
| 35  | [patch_add_cognitive_mode_enum.py](patch_add_cognitive_mode_enum.py)                                                                 | Dodanie CognitiveMode enum            |
| 36  | [patch_add_get_advanced_cognitive_engine.py](patch_add_get_advanced_cognitive_engine.py)                                             | Dodanie get_advanced_cognitive_engine |
| 37  | [patch_app_nonfatal_failed_routers.py](patch_app_nonfatal_failed_routers.py)                                                         | Non-fatal router failures             |
| 38  | [patch_bootstrap_advanced_cognitive_types.py](patch_bootstrap_advanced_cognitive_types.py)                                           | Bootstrap typów                       |
| 39  | [patch_chatbox_buffer.py](patch_chatbox_buffer.py)                                                                                   | Chatbox buffer fix                    |
| 40  | [patch_disable_any_router_exception_handler_router_vars.py](patch_disable_any_router_exception_handler_router_vars.py)               | Disable exception handlers            |
| 41  | [patch_disable_apirouter_exception_handler_repo_wide.py](patch_disable_apirouter_exception_handler_repo_wide.py)                     | Repo-wide disable                     |
| 42  | [patch_fix_deploy_py_fstring_backslash.py](patch_fix_deploy_py_fstring_backslash.py)                                                 | Deploy.py f-string fix                |
| 43  | [patch_fix_future_import_position_in_advanced_cognitive_engine.py](patch_fix_future_import_position_in_advanced_cognitive_engine.py) | Future import position                |
| 44  | [patch_fix_writing_fstring_resub_cat_tag.py](patch_fix_writing_fstring_resub_cat_tag.py)                                             | Writing f-string fix                  |
| 45  | [patch_fix_writing_hashtags_fstring_regex.py](patch_fix_writing_hashtags_fstring_regex.py)                                           | Hashtags regex fix                    |
| 46  | [patch_force_alias_get_advanced_cognitive_engine.py](patch_force_alias_get_advanced_cognitive_engine.py)                             | Force alias                           |
| 47  | [patch_move_cognitive_mode_to_top.py](patch_move_cognitive_mode_to_top.py)                                                           | Move CognitiveMode                    |
| 48  | [patch_mrd_fix_compile_and_failed_routers.py](patch_mrd_fix_compile_and_failed_routers.py)                                           | Compile fix                           |
| 49  | [patch_mrd_fix_fstrings_and_router_exception_handler.py](patch_mrd_fix_fstrings_and_router_exception_handler.py)                     | F-strings fix                         |
| 50  | [patch_nonfatal_failed_routers_everywhere.py](patch_nonfatal_failed_routers_everywhere.py)                                           | Non-fatal everywhere                  |
| 51  | [patch_stream_finaldelta.py](patch_stream_finaldelta.py)                                                                             | Stream final delta                    |
| 52  | [patch_stream_pingflush.py](patch_stream_pingflush.py)                                                                               | Stream ping flush                     |

#### SKRYPTY FIX (6 PLIKÓW)

| #   | Plik                                                                       | Cel fixa                        |
| --- | -------------------------------------------------------------------------- | ------------------------------- |
| 53  | [fix_conversations_tables.py](fix_conversations_tables.py)                 | Fix tabel konwersacji           |
| 54  | [fix_hier_mem_await.py](fix_hier_mem_await.py)                             | Fix await w hierarchical memory |
| 55  | [fix_openai_compat_boundary_hard.py](fix_openai_compat_boundary_hard.py)   | OpenAI compat boundary          |
| 56  | [fix_openai_compat_broken_strings.py](fix_openai_compat_broken_strings.py) | Broken strings fix              |

#### SKRYPTY TOOLS (8 PLIKÓW)

| #   | Plik                                                                                                   | Cel                |
| --- | ------------------------------------------------------------------------------------------------------ | ------------------ |
| 57  | [tools_fix_hybrid_primary.py](tools_fix_hybrid_primary.py)                                             | Hybrid primary fix |
| 58  | [tools_fix_hybrid_primary_v2.py](tools_fix_hybrid_primary_v2.py)                                       | Hybrid primary v2  |
| 59  | [tools_fix_hybrid_router.py](tools_fix_hybrid_router.py)                                               | Hybrid router fix  |
| 60  | [tools_patch_app_aliases.py](tools_patch_app_aliases.py)                                               | App aliases patch  |
| 61  | [tools_patch_app_get_automation_summary.py](tools_patch_app_get_automation_summary.py)                 | Automation summary |
| 62  | [tools_patch_app_get_automation_summary_refresh.py](tools_patch_app_get_automation_summary_refresh.py) | Automation refresh |
| 63  | [tools_patch_hybrid_callsite.py](tools_patch_hybrid_callsite.py)                                       | Hybrid callsite    |
| 64  | [tools_patch_hybrid_call_helper.py](tools_patch_hybrid_call_helper.py)                                 | Call helper        |

#### AUDYT/DOKUMENTY

| #   | Plik                                                 | Typ             |
| --- | ---------------------------------------------------- | --------------- |
| 65  | [audit_adv_cog_extract.py](audit_adv_cog_extract.py) | Skrypt audytowy |

---

### 2.2. CORE `mrd/core/` (53 pliki .py)

#### ENTRYPOINT

| #   | Plik                  | Linie | Opis                                               |
| --- | --------------------- | ----- | -------------------------------------------------- |
| 1   | [app.py](core/app.py) | 646   | ⚠️ ALTERNATYWNY ENTRYPOINT (z `uvicorn.run` L:639) |

#### KONFIGURACJA I AUTH

| #   | Plik                            | Linie | Eksportuje                                   | Importowany przez |
| --- | ------------------------------- | ----- | -------------------------------------------- | ----------------- |
| 2   | [**init**.py](core/__init__.py) | ~10   | (pusty lub re-export)                        | -                 |
| 3   | [config.py](core/config.py)     | ~200  | `AUTH_TOKEN`, `LLM_*`, `MEM_DB`, `WORKSPACE` | Prawie wszystko   |
| 4   | [auth.py](core/auth.py)         | ~100  | `auth_dependency`, `verify_token`            | Endpointy         |

#### LLM I PAMIĘĆ

| #   | Plik                                                  | Linie | Eksportuje                                                                   | Importowany przez                   |
| --- | ----------------------------------------------------- | ----- | ---------------------------------------------------------------------------- | ----------------------------------- |
| 5   | [llm.py](core/llm.py)                                 | ~500  | `call_llm`, `call_llm_stream`, `LLMClient`                                   | cognitive_engine, research, writing |
| 6   | [memory.py](core/memory.py)                           | 2407  | `UnifiedMemorySystem`, `ltm_add`, `stm_*`, `psy_*`, `cache_get`, `cache_put` | Prawie wszystko                     |
| 7   | [hierarchical_memory.py](core/hierarchical_memory.py) | ~800  | `HierarchicalMemorySystem`                                                   | cognitive_engine                    |
| 8   | [memory_store.py](core/memory_store.py)               | ~300  | `MemoryStore`                                                                | memory_endpoint                     |
| 9   | [memory_endpoint.py](core/memory_endpoint.py)         | ~200  | Router `/api/memory`                                                         | app.py ✅                           |
| 10  | [memory_persistence.py](core/memory_persistence.py)   | ~200  | Persistence helpers                                                          | memory.py                           |
| 11  | [memory_summarizer.py](core/memory_summarizer.py)     | ~200  | Summarization                                                                | memory.py                           |

#### SILNIKI KOGNITYWNE

| #   | Plik                                                              | Linie | Eksportuje                           | Importowany przez              |
| --- | ----------------------------------------------------------------- | ----- | ------------------------------------ | ------------------------------ |
| 12  | [cognitive_engine.py](core/cognitive_engine.py)                   | ~1500 | `CognitiveEngine`, `process_message` | assistant_endpoint             |
| 13  | [advanced_cognitive_engine.py](core/advanced_cognitive_engine.py) | ~800  | `AdvancedCognitiveEngine`            | cognitive_engine (opcjonalnie) |
| 14  | [cognitive_endpoint.py](core/cognitive_endpoint.py)               | ~200  | Router `/api/cognitive`              | app.py ✅                      |

#### NARZĘDZIA AI

| #   | Plik                                              | Linie | Eksportuje                                | Importowany przez        |
| --- | ------------------------------------------------- | ----- | ----------------------------------------- | ------------------------ |
| 15  | [tools_registry.py](core/tools_registry.py)       | ~1000 | `get_all_tools`, 121 tools jako functions | cognitive_engine, app.py |
| 16  | [tools.py](core/tools.py)                         | ~500  | Tool implementations                      | tools_registry           |
| 17  | [intent_dispatcher.py](core/intent_dispatcher.py) | ~400  | `FAST_PATH_HANDLERS`, dispatch            | cognitive_engine         |
| 18  | [executor.py](core/executor.py)                   | ~300  | `Programista` class                       | programista_endpoint     |

#### RESEARCH I SEARCH

| #   | Plik                                                        | Linie | Eksportuje                              | Importowany przez                   |
| --- | ----------------------------------------------------------- | ----- | --------------------------------------- | ----------------------------------- |
| 19  | [research.py](core/research.py)                             | 1247  | `web_search`, `autonauka`, `scrape_url` | cognitive_engine, research_endpoint |
| 20  | [research_endpoint.py](core/research_endpoint.py)           | ~200  | Router `/api/research`                  | ❌ NIE ŁADOWANY przez app.py        |
| 21  | [brave_search.py](core/brave_search.py)                     | ~250  | `brave_search`                          | research.py                         |
| 22  | [tavily_search.py](core/tavily_search.py)                   | ~160  | `tavily_search`                         | research.py                         |
| 23  | [hybrid_search_endpoint.py](core/hybrid_search_endpoint.py) | ~200  | Router `/api/search`                    | app.py ✅                           |

#### PSYCHOLOGIA I REFLEKSJA

| #   | Plik                                                  | Linie | Eksportuje               | Importowany przez                   |
| --- | ----------------------------------------------------- | ----- | ------------------------ | ----------------------------------- |
| 24  | [advanced_psychology.py](core/advanced_psychology.py) | ~500  | `AdvancedPsychology`     | cognitive_engine                    |
| 25  | [psyche_endpoint.py](core/psyche_endpoint.py)         | ~200  | Router `/api/psyche`     | ❌ NIE ŁADOWANY (tylko core/app.py) |
| 26  | [self_reflection.py](core/self_reflection.py)         | ~700  | `SelfReflection`         | reflection_endpoint                 |
| 27  | [reflection_endpoint.py](core/reflection_endpoint.py) | ~200  | Router `/api/reflection` | app.py ✅                           |

#### PISANIE I KREACJA

| #   | Plik                          | Linie | Eksportuje                       | Importowany przez        |
| --- | ----------------------------- | ----- | -------------------------------- | ------------------------ |
| 28  | [writing.py](core/writing.py) | ~800  | `generate_text`, `WritingEngine` | writing_endpoint         |
| 29  | [prompt.py](core/prompt.py)   | ~300  | `build_prompt`, `SYSTEM_PROMPT`  | llm.py, cognitive_engine |

#### ASYSTENCI SPECJALISTYCZNI

| #   | Plik                                                        | Linie | Router prefix         | Status                                           |
| --- | ----------------------------------------------------------- | ----- | --------------------- | ------------------------------------------------ |
| 30  | [assistant_endpoint.py](core/assistant_endpoint.py)         | ~400  | `/api/chat`           | ✅ Ładowany przez app.py                         |
| 31  | [negocjator_endpoint.py](core/negocjator_endpoint.py)       | ~300  | `/api/negocjator`     | ✅ Ładowany przez app.py                         |
| 32  | [legal_office_endpoint.py](core/legal_office_endpoint.py)   | ~400  | `/api/legal`          | ✅ Ładowany przez app.py                         |
| 33  | [hacker_endpoint.py](core/hacker_endpoint.py)               | ~300  | `/api/hacker`         | ❌ NIE ŁADOWANY                                  |
| 34  | [chat_advanced_endpoint.py](core/chat_advanced_endpoint.py) | ~200  | `/core/chat/advanced` | ❌ NIE ŁADOWANY                                  |
| 35  | [auction_endpoint.py](core/auction_endpoint.py)             | ~200  | `/api/auction`        | ❌ NIE ŁADOWANY                                  |
| 36  | [admin_endpoint.py](core/admin_endpoint.py)                 | ~300  | `/api/admin`          | ❌ NIE ŁADOWANY przez app.py (tylko core/app.py) |

#### BATCH I PARALLEL

| #   | Plik                                            | Linie | Eksportuje          | Importowany przez |
| --- | ----------------------------------------------- | ----- | ------------------- | ----------------- |
| 37  | [batch_processing.py](core/batch_processing.py) | ~540  | `BatchProcessor`    | batch_endpoint    |
| 38  | [batch_endpoint.py](core/batch_endpoint.py)     | ~200  | Router `/api/batch` | app.py ✅         |
| 39  | [parallel.py](core/parallel.py)                 | ~200  | Parallel execution  | batch_processing  |

#### MONITORING I MIDDLEWARE

| #   | Plik                                                  | Linie | Eksportuje                       | Importowany przez           |
| --- | ----------------------------------------------------- | ----- | -------------------------------- | --------------------------- |
| 40  | [metrics.py](core/metrics.py)                         | ~200  | `PROMETHEUS_AVAILABLE`, counters | app.py, prometheus_endpoint |
| 41  | [prometheus_endpoint.py](core/prometheus_endpoint.py) | ~100  | Router (no prefix)               | app.py ✅                   |
| 42  | [middleware.py](core/middleware.py)                   | ~200  | Middleware classes               | ❌ NIE UŻYWANE              |
| 43  | [redis_middleware.py](core/redis_middleware.py)       | ~150  | Redis cache                      | memory.py (opcjonalnie)     |

#### ADVANCED MODULES

| #   | Plik                                                  | Linie | Eksportuje              | Status               |
| --- | ----------------------------------------------------- | ----- | ----------------------- | -------------------- |
| 44  | [advanced_memory.py](core/advanced_memory.py)         | ~600  | `AdvancedMemoryManager` | ❓ Częściowo używane |
| 45  | [advanced_llm.py](core/advanced_llm.py)               | ~400  | `AdvancedLLM`           | ❓ Częściowo używane |
| 46  | [advanced_learning.py](core/advanced_learning.py)     | ~500  | `AdvancedLearning`      | ❓ Częściowo używane |
| 47  | [advanced_proactive.py](core/advanced_proactive.py)   | ~400  | `AdvancedProactive`     | suggestions_endpoint |
| 48  | [advanced_autorouter.py](core/advanced_autorouter.py) | ~300  | `AdvancedAutorouter`    | ❓ NIE UŻYWANE       |

#### INNE MODUŁY

| #   | Plik                                                            | Linie | Eksportuje                | Status           |
| --- | --------------------------------------------------------------- | ----- | ------------------------- | ---------------- |
| 49  | [helpers.py](core/helpers.py)                                   | ~300  | Utility functions         | Wszędzie         |
| 50  | [semantic.py](core/semantic.py)                                 | ~400  | Semantic analysis         | cognitive_engine |
| 51  | [sessions.py](core/sessions.py)                                 | ~200  | Session management        | ❓               |
| 52  | [context_awareness.py](core/context_awareness.py)               | ~300  | Context detection         | ❓               |
| 53  | [smart_context.py](core/smart_context.py)                       | ~250  | Smart context             | ❓               |
| 54  | [inner_language.py](core/inner_language.py)                     | ~1350 | Inner language system     | ❓               |
| 55  | [knowledge_compression.py](core/knowledge_compression.py)       | ~300  | Knowledge compression     | ❓               |
| 56  | [user_model.py](core/user_model.py)                             | ~250  | User modeling             | ❓               |
| 57  | [response_adapter.py](core/response_adapter.py)                 | ~200  | Response adaptation       | ❓               |
| 58  | [nlp_processor.py](core/nlp_processor.py)                       | ~560  | NLP processing            | ❓               |
| 59  | [conversation_analytics.py](core/conversation_analytics.py)     | ~300  | Analytics                 | ❓               |
| 60  | [fact_validation.py](core/fact_validation.py)                   | ~200  | Fact checking             | ❓               |
| 61  | [future_predictor.py](core/future_predictor.py)                 | ~200  | Prediction                | ❓               |
| 62  | [multi_agent_orchestrator.py](core/multi_agent_orchestrator.py) | ~1060 | Multi-agent               | ❓               |
| 63  | [autoroute.py](core/autoroute.py)                               | ~200  | Auto-routing              | ❓               |
| 64  | [ai_auction.py](core/ai_auction.py)                             | ~300  | AI auction                | auction_endpoint |
| 65  | [suggestions_endpoint.py](core/suggestions_endpoint.py)         | ~200  | Router `/api/suggestions` | ❓ duplikat root |

#### TESTY CORE

| #   | Plik                                                        | Typ  |
| --- | ----------------------------------------------------------- | ---- |
| 66  | [stress_test_system.py](core/stress_test_system.py)         | Test |
| 67  | [ultra_destruction_test.py](core/ultra_destruction_test.py) | Test |

---

### 2.3. TESTS `mrd/tests/` (11 plików)

| #   | Plik                                                                 | Typ      | Testuje               |
| --- | -------------------------------------------------------------------- | -------- | --------------------- |
| 1   | [**init**.py](tests/__init__.py)                                     | Init     | -                     |
| 2   | [conftest.py](tests/conftest.py)                                     | Fixtures | pytest fixtures       |
| 3   | [test_api_endpoints.py](tests/test_api_endpoints.py)                 | Test     | API endpoints         |
| 4   | [test_batch_processing.py](tests/test_batch_processing.py)           | Test     | Batch processing      |
| 5   | [test_core_modules.py](tests/test_core_modules.py)                   | Test     | Core modules          |
| 6   | [test_hierarchical_memory.py](tests/test_hierarchical_memory.py)     | Test     | Hierarchical memory   |
| 7   | [test_integration.py](tests/test_integration.py)                     | Test     | Integration           |
| 8   | [test_proactive_suggestions.py](tests/test_proactive_suggestions.py) | Test     | Proactive suggestions |
| 9   | [test_vision_tts.py](tests/test_vision_tts.py)                       | Test     | Vision + TTS          |
| 10  | [test_writing_endpoint.py](tests/test_writing_endpoint.py)           | Test     | Writing endpoint      |

---

### 2.4. TOOLS `mrd/tools/` (2 pliki)

| #   | Plik                                               | Typ   | Opis                      |
| --- | -------------------------------------------------- | ----- | ------------------------- |
| 1   | [mrd_repo_index.py](tools/mrd_repo_index.py)       | Util  | Indeksowanie repozytorium |
| 2   | [patch_hybrid_pick.py](tools/patch_hybrid_pick.py) | Patch | Hybrid pick patch         |

---

### 2.5. SCRIPTS `mrd/scripts/` (1 plik)

| #   | Plik                                                   | Typ  | Opis                   |
| --- | ------------------------------------------------------ | ---- | ---------------------- |
| 1   | [check_requirements.py](scripts/check_requirements.py) | Util | Sprawdzanie zależności |

---

## 3. ENTRYPOINTY - ANALIZA

### 3.1. PRODUKCYJNE ENTRYPOINTY (z `uvicorn.run` lub `FastAPI()`)

| #   | Plik              | Linia         | Mechanizm                                         | Status          |
| --- | ----------------- | ------------- | ------------------------------------------------- | --------------- |
| 1   | **app.py** (root) | L:51          | `FastAPI(title="Mordzix AI")` + dynamiczny import | ⭐ **GŁÓWNY**   |
| 2   | **core/app.py**   | L:198 + L:639 | `FastAPI()` + `uvicorn.run()`                     | ⚠️ ALTERNATYWNY |

### 3.2. SKRYPTY Z `__main__` (51 plików)

| Kategoria    | Ilość | Pliki                                                                                                                                                                                                                   |
| ------------ | ----- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Patche       | 18    | `patch_*.py`                                                                                                                                                                                                            |
| Fixy         | 4     | `fix_*.py`                                                                                                                                                                                                              |
| Tools        | 8     | `tools_*.py`                                                                                                                                                                                                            |
| Testy        | 6     | `*_test*.py`, `stress_test_*.py`                                                                                                                                                                                        |
| Deploy       | 2     | `deploy.py`, `print_routes.py`                                                                                                                                                                                          |
| Utils        | 3     | `set_memory_db_env.py`, `scripts/check_requirements.py`, `audit_adv_cog_extract.py`                                                                                                                                     |
| Core modules | 10    | `core/batch_processing.py`, `core/brave_search.py`, `core/inner_language.py`, `core/multi_agent_orchestrator.py`, `core/nlp_processor.py`, `core/self_reflection.py`, `core/tavily_search.py`, `core/tools_registry.py` |

---

## 4. ENTRYPOINT TRUTH - DECYZJA

### ⭐ PRAWDZIWY ENTRYPOINT: `mrd/app.py`

**Dowód:**

- Linia 51: `app = FastAPI(title=APP_TITLE, version=APP_VERSION, docs_url="/docs", redoc_url="/redoc")`
- Linie 100-145: Dynamiczne ładowanie 16 routerów
- Brak `if __name__ == "__main__"` - wymaga zewnętrznego `uvicorn app:app`
- Start scripts (`start.sh`, `start_api.sh`) używają `uvicorn app:app`

**Ładowane routery (zweryfikowane import testem):**

```
✅ openai_compat         → /v1/*
✅ assistant_simple      → /api/chat/*
✅ stt_endpoint          → /api/stt/*
✅ tts_endpoint          → /api/tts/*
✅ suggestions_endpoint  → /api/suggestions/*
✅ internal_endpoint     → /api/internal/*
✅ files_endpoint        → /api/files/*
✅ routers               → /api/routers/*
✅ core.assistant_endpoint     → /api/chat/* (advanced)
✅ core.memory_endpoint        → /api/memory/*
✅ core.cognitive_endpoint     → /api/cognitive/*
✅ core.negocjator_endpoint    → /api/negocjator/*
✅ core.reflection_endpoint    → /api/reflection/*
✅ core.legal_office_endpoint  → /api/legal/*
✅ core.hybrid_search_endpoint → /api/search/*
✅ core.batch_endpoint         → /api/batch/*
✅ core.prometheus_endpoint    → /api/prometheus/*
```

### ⚠️ ALTERNATYWNY ENTRYPOINT: `mrd/core/app.py`

**Dowód:**

- Linia 198: `app = FastAPI(title="Mordzix AI", version="5.0.0")`
- Linia 639: `uvicorn.run("app:app", ...)`
- Ładuje INNE routery niż root app.py

**NIE UŻYWAĆ** z katalogu root - importy są relatywne do `core/`.

---

## 5. ROUTERY NIEPODPIĘTE W app.py (WYMAGA ANALIZY PKT 07)

**UWAGA:** Status "NIEPODPIĘTE" NIE oznacza automatycznie "ORPHAN/MARTWE". Pliki mogą być importowane dynamicznie lub używane przez alternatywny entrypoint. Ostateczna klasyfikacja wymaga analizy import-grafu w pkt 07.

| Plik                                                             | Router prefix                 | Problem                     | Naprawa                 |
| ---------------------------------------------------------------- | ----------------------------- | --------------------------- | ----------------------- |
| [writing_endpoint.py](writing_endpoint.py)                       | `/api/writing`                | Nie w `app.py` root_modules | Dodać do `app.py` L:100 |
| [psyche_endpoint.py](psyche_endpoint.py)                         | `/api/psyche`                 | Nie w `app.py`              | Dodać do `app.py`       |
| [travel_endpoint.py](travel_endpoint.py)                         | `/api/travel`                 | Nie w `app.py`              | Dodać do `app.py`       |
| [research_endpoint.py](research_endpoint.py)                     | `/api/research`               | Nie w `app.py`              | Dodać do `app.py`       |
| [programista_endpoint.py](programista_endpoint.py)               | `/api/code`                   | Nie w `app.py`              | Dodać do `app.py`       |
| [nlp_endpoint.py](nlp_endpoint.py)                               | `/api/nlp`                    | Nigdzie nie ładowany        | Dodać do `app.py`       |
| [writer_pro.py](writer_pro.py)                                   | `/api/writer` (writer_router) | Nie w `app.py` + zła nazwa  | Kandydat do pkt 07      |
| [core/hacker_endpoint.py](core/hacker_endpoint.py)               | `/api/hacker`                 | Nie w `app.py`              | Kandydat do pkt 07      |
| [core/chat_advanced_endpoint.py](core/chat_advanced_endpoint.py) | `/core/chat/advanced`         | Nie w `app.py`              | Kandydat do pkt 07      |
| [core/auction_endpoint.py](core/auction_endpoint.py)             | `/api/auction`                | Nie w `app.py`              | Kandydat do pkt 07      |
| [core/admin_endpoint.py](core/admin_endpoint.py)                 | `/api/admin`                  | Nie w `app.py`              | Dodać do `app.py`       |
| [core/research_endpoint.py](core/research_endpoint.py)           | `/api/research`               | Duplikat root (CONFLICT P0) | Unifikacja w pkt 07     |
| [core/psyche_endpoint.py](core/psyche_endpoint.py)               | `/api/psyche`                 | Duplikat root (CONFLICT P0) | Unifikacja w pkt 07     |
| [core/suggestions_endpoint.py](core/suggestions_endpoint.py)     | `/api/suggestions`            | Duplikat root (CONFLICT P0) | Unifikacja w pkt 07     |

---

## 6. DUPLIKATY PLIKÓW (ROOT vs CORE) — KANDYDACI DO ARCHIWIZACJI

**WAŻNE:** Poniższe to TYLKO kandydaci. Żadne usuwanie bez dowodu z import-grafu (pkt 07).

| Plik w ROOT                 | Plik w CORE                      | Status                             | Wymagana weryfikacja |
| --------------------------- | -------------------------------- | ---------------------------------- | -------------------- |
| `research.py`               | `core/research.py`               | Duplikat                           | Import-graf pkt 07   |
| `hierarchical_memory.py`    | `core/hierarchical_memory.py`    | Duplikat                           | Import-graf pkt 07   |
| `hybrid_search_endpoint.py` | `core/hybrid_search_endpoint.py` | ROOT re-eksportuje CORE            | Import-graf pkt 07   |
| `research_endpoint.py`      | `core/research_endpoint.py`      | CONFLICT(P0) - ten sam prefix      | Pkt 03 + pkt 07      |
| `psyche_endpoint.py`        | `core/psyche_endpoint.py`        | CONFLICT(P0) - ten sam prefix      | Pkt 03 + pkt 07      |
| `suggestions_endpoint.py`   | `core/suggestions_endpoint.py`   | Root podpięty, core nie            | Pkt 07               |
| `prometheus_endpoint.py`    | `core/prometheus_endpoint.py`    | Core podpięty z prefix             | Pkt 07               |
| `stress_test_system.py`     | `core/stress_test_system.py`     | Testy - kandydaci do przeniesienia | Pkt 07               |
| `ultra_destruction_test.py` | `core/ultra_destruction_test.py` | Testy - kandydaci do przeniesienia | Pkt 07               |

---

## 7. PODSUMOWANIE MAPY

| Metryka                     | Wartość                       | Dowód                                 |
| --------------------------- | ----------------------------- | ------------------------------------- |
| **Pliki .py łącznie**       | 145                           | `Get-ChildItem -Recurse -Filter *.py` |
| **Pliki w ROOT**            | 65                            | 01_FILES_FULL_LIST.md                 |
| **Pliki w CORE**            | 67                            | 01_FILES_FULL_LIST.md                 |
| **Pliki w TESTS**           | 10                            | 01_FILES_FULL_LIST.md                 |
| **Pliki w TOOLS**           | 2                             | 01_FILES_FULL_LIST.md                 |
| **Pliki w SCRIPTS**         | 1                             | 01_FILES_FULL_LIST.md                 |
| **Entrypointy produkcyjne** | 2 (app.py ⭐, core/app.py ⚠️) | Sekcja 3.1                            |
| **Routery ładowane**        | 17 (1 hardcoded + 16 dynamic) | app.py L:53 + L:100-145               |

---

## 8. WERYFIKACJA RUNTIME

**Poprawna komenda testowa (sprawdza faktycznie załadowane routery):**

```bash
cd c:\Users\48501\Desktop\mrd
# Sprawdź status routerów przez wbudowany endpoint:
curl http://localhost:8000/api/routers/status
```

**Oczekiwany wynik (JSON):**

```json
{
  "loaded": [{"module": "assistant_simple", "name": "Chat (Commercial)"}, ...],
  "failed": [],
  "ts": ...
}
```

**Alternatywna weryfikacja - lista endpointów:**

```bash
curl http://localhost:8000/api/endpoints/list | jq '.count'
```

**Źródło:** [app.py](../app.py) L:164-165 (`/api/routers/status`) i L:168-175 (`/api/endpoints/list`)

---

## 9. DOWODY (CITATIONS)

### 9.1 Liczba plików .py

**Komenda (Linux):**

```bash
$ find . -type f -name "*.py" -print | wc -l
145
```

**Podział per katalog:**

```bash
$ find . -type f -name "*.py" -printf '%h\n' | sort | uniq -c | sort -nr
     67 ./core
     65 .
     10 ./tests
      2 ./tools
      1 ./scripts
```

**Pełna lista:** [01_FILES_FULL_LIST.md](01_FILES_FULL_LIST.md)

### 9.2 Entrypoint #1: ./app.py

**Cytaty z [./app.py](../app.py):**

- **L:51** — Tworzenie aplikacji FastAPI:

  ```python
  app = FastAPI(title=APP_TITLE, version=APP_VERSION, docs_url="/docs", redoc_url="/redoc")
  ```

- **L:53** — Pierwszy include (hardcoded):

  ```python
  app.include_router(openai_compat_router)
  ```

- **L:100-108** — Lista `root_modules` (7 modułów):

  ```python
  root_modules = [
      ("assistant_simple", "Chat (Commercial)"),
      ("stt_endpoint", "STT (Speech-to-Text)"),
      ("tts_endpoint", "TTS (Text-to-Speech)"),
      ("suggestions_endpoint", "Suggestions"),
      ("internal_endpoint", "Internal"),
      ("files_endpoint", "Files (Advanced)"),
      ("routers", "Admin/Debug"),
  ]
  ```

- **L:127-137** — Lista `core_modules` (9 modułów):

  ```python
  core_modules = [
      ("core.assistant_endpoint", "Chat (Advanced) [core]"),
      ("core.memory_endpoint", "Memory [core]"),
      ("core.cognitive_endpoint", "Cognitive [core]"),
      ("core.negocjator_endpoint", "Negotiator [core]"),
      ("core.reflection_endpoint", "Reflection [core]"),
      ("core.legal_office_endpoint", "Legal Office [core]"),
      ("core.hybrid_search_endpoint", "Hybrid Search [core]"),
      ("core.batch_endpoint", "Batch Processing [core]"),
      ("core.prometheus_endpoint", "Metrics [core]"),
  ]
  ```

- **L:82-89** — Mechanizm ładowania (szuka atrybutu `router`):
  ```python
  def _try_import_router(modname: str) -> Tuple[Optional[Any], Optional[str]]:
      try:
          m = importlib.import_module(modname)
          r = getattr(m, "router", None)
          if r is None:
              return None, "no router attr"
          return r, None
  ```

### 9.3 Kolejność include_router() w app.py (TRUTH)

**WNIOSEK:** W FastAPI przy konfliktach path+method **PIERWSZY zarejestrowany wygrywa** (Starlette routing).

**Kolejność rejestracji w app.py:**

| Pozycja | Linia       | Moduł                            | Prefix             |
| ------- | ----------- | -------------------------------- | ------------------ |
| 1       | L:53        | openai_compat_router (hardcoded) | `/v1`              |
| 2       | L:116 pętla | assistant_simple                 | `/api/chat`        |
| 3       | L:116 pętla | stt_endpoint                     | `/api/stt`         |
| 4       | L:116 pętla | tts_endpoint                     | `/api/tts`         |
| 5       | L:116 pętla | suggestions_endpoint             | `/api/suggestions` |
| 6       | L:116 pętla | internal_endpoint                | `/api/internal`    |
| 7       | L:116 pętla | files_endpoint                   | `/api/files`       |
| 8       | L:116 pętla | routers                          | `/api/routers`     |
| 9       | L:149 pętla | core.assistant_endpoint          | `/api/chat`        |
| 10      | L:149 pętla | core.memory_endpoint             | `/api/memory`      |
| 11      | L:149 pętla | core.cognitive_endpoint          | `/api/cognitive`   |
| 12      | L:149 pętla | core.negocjator_endpoint         | `/api/negocjator`  |
| 13      | L:149 pętla | core.reflection_endpoint         | `/api/reflection`  |
| 14      | L:149 pętla | core.legal_office_endpoint       | `/api/legal`       |
| 15      | L:149 pętla | core.hybrid_search_endpoint      | `/api/search`      |
| 16      | L:149 pętla | core.batch_endpoint              | `/api/batch`       |
| 17      | L:149 pętla | core.prometheus_endpoint         | `/api/prometheus`  |

### 9.4 Konflikt /api/chat/assistant — KTO WYGRYWA?

**Problem:** Oba moduły mają `prefix="/api/chat"` i endpoint `POST /assistant`:

- `assistant_simple.py` → L:254: `@router.post("/assistant")`
- `core/assistant_endpoint.py` → L:49: `@router.post("/assistant", response_model=ChatResponse)`

**Odpowiedź:** `assistant_simple` wygrywa, bo jest ładowany PRZED `core.assistant_endpoint` (pozycja 2 vs 9).

**Weryfikacja runtime:**

```bash
# Uruchom serwer i sprawdź który endpoint odpowiada:
curl -X POST http://localhost:8000/api/chat/assistant -H "Content-Type: application/json" -d '{"message":"test"}'
# Sprawdź response - czy ma pola z assistant_simple czy core/assistant_endpoint
```

### 9.5 Klasyfikacja ACTIVE/DEAD

**Definicje używane w tym dokumencie:**

| Status                  | Definicja                                                                                 |
| ----------------------- | ----------------------------------------------------------------------------------------- |
| ✅ PODPIĘTE w app.py    | Router jest w `root_modules` lub `core_modules` w [app.py](../app.py) L:100-145           |
| ⚠️ NIEPODPIĘTE w app.py | Router NIE jest w listach, ale może być używany przez core/app.py lub importowany inaczej |
| ❓ WYMAGA PKT 07        | Ostateczna klasyfikacja (ORPHAN/LEGACY) wymaga analizy import-grafu                       |

**ZAKAZ:** W pkt 01-03 nie rozstrzygamy czy plik jest "martwy" ani nie rekomendujemy usunięcia.

---

**STOP — sprawdź ten punkt. Czy coś poprawić/doprecyzować? Czy mam dodać coś jeszcze? Jeśli OK, przechodzę do następnego punktu: `AUDYT/02_MIX_ROUTEROW_UNIFIKACJA2.md`.**
