# 🗺️ PEŁNA MAPA PROJEKTU MRD - AUDYT 145 PLIKÓW .PY

**Data audytu:** 26 grudnia 2025  
**Autor:** Audyt automatyczny

---

## 📊 PODSUMOWANIE STATYSTYK

| Kategoria                               | Liczba |
| --------------------------------------- | ------ |
| **Pliki .py ogółem**                    | 145    |
| **Pliki z kodem produkcyjnym**          | ~80    |
| **Pliki narzędziowe (patch/fix/tools)** | ~35    |
| **Pliki testowe**                       | 10     |
| **Entrypoints z `__main__`**            | 44+    |
| **Routery FastAPI**                     | 34     |
| **Orphan files (nieimportowane)**       | 28+    |

---

## 🏗️ STRUKTURA KATALOGÓW

| Katalog        | Rola                                                  | Liczba plików |
| -------------- | ----------------------------------------------------- | ------------- |
| `mrd/` (root)  | Główny entrypoint, routery HTTP, utility, patche      | ~55           |
| `mrd/core/`    | Biblioteka rdzenia: LLM, memory, cognitive, endpoints | ~65           |
| `mrd/tests/`   | Testy pytest                                          | 10            |
| `mrd/scripts/` | Skrypty pomocnicze                                    | 1             |
| `mrd/tools/`   | Narzędzia deweloperskie                               | 2             |

---

## 📋 PEŁNA TABELA WSZYSTKICH PLIKÓW .PY

### 1️⃣ PLIKI ROOT (`mrd/`)

| Plik                                                   | Typ                  | Entrypoint?        | Router?               | Główne importy                                           | Eksportuje                                      | Importowany przez                             |
| ------------------------------------------------------ | -------------------- | ------------------ | --------------------- | -------------------------------------------------------- | ----------------------------------------------- | --------------------------------------------- |
| [app.py](app.py)                                       | **MAIN ENTRYPOINT**  | ❌ (brak **main**) | ❌ (to app FastAPI)   | `openai_compat`, `assistant_simple`, `routers`, `core.*` | `app` (FastAPI)                                 | **Główny serwer**                             |
| [openai_compat.py](openai_compat.py)                   | Router               | ❌                 | ✅ `/v1`              | `httpx`, `fastapi`                                       | `router`                                        | `app.py`                                      |
| [assistant_simple.py](assistant_simple.py)             | Router (Chat)        | ❌                 | ✅ `/api/chat`        | `httpx`, `pydantic`, sqlite3                             | `router`                                        | `app.py`                                      |
| [assistant_endpoint.py](assistant_endpoint.py)         | Router (Chat)        | ❌                 | ✅ `/api/chat`        | `core.cognitive_engine`, `core.memory`                   | `router`                                        | **ORPHAN** (nie użyty w app.py)               |
| [routers.py](routers.py)                               | Router (Admin/Debug) | ❌                 | ✅ `/api/routers`     | `core.config`, `core.auth`, `core.memory`                | `router`                                        | `app.py`                                      |
| [stt_endpoint.py](stt_endpoint.py)                     | Router (STT)         | ❌                 | ✅ `/api/stt`         | `fastapi`, `pydantic`                                    | `router`                                        | `app.py`                                      |
| [tts_endpoint.py](tts_endpoint.py)                     | Router (TTS)         | ❌                 | ✅ `/api/tts`         | `fastapi`, `pydantic`                                    | `router`                                        | `app.py`                                      |
| [tts_elevenlabs.py](tts_elevenlabs.py)                 | Library              | ❌                 | ❌                    | `core.config`, `core.helpers`                            | `text_to_speech`, `get_voices`, `POLISH_VOICES` | `tests/test_vision_tts.py`                    |
| [suggestions_endpoint.py](suggestions_endpoint.py)     | Router               | ❌                 | ✅ `/api/suggestions` | `core.auth`, `core.advanced_proactive`                   | `router`                                        | `app.py`                                      |
| [internal_endpoint.py](internal_endpoint.py)           | Router               | ❌                 | ✅ `/api/internal`    | `fastapi`                                                | `router`                                        | `app.py`                                      |
| [files_endpoint.py](files_endpoint.py)                 | Router               | ❌                 | ✅ `/api/files`       | `fastapi`, `pydantic`                                    | `router`                                        | `app.py`                                      |
| [writing_endpoint.py](writing_endpoint.py)             | Router               | ❌                 | ✅ `/api/writing`     | `core.writing`                                           | `router`                                        | **ORPHAN**                                    |
| [psyche_endpoint.py](psyche_endpoint.py)               | Router               | ❌                 | ✅ `/api/psyche`      | `core.memory`, `core.auth`, `core.advanced_psychology`   | `router`                                        | **ORPHAN**                                    |
| [travel_endpoint.py](travel_endpoint.py)               | Router               | ❌                 | ✅ `/api/travel`      | `core.research`, `core.auth`                             | `router`                                        | **ORPHAN**                                    |
| [research_endpoint.py](research_endpoint.py)           | Router               | ❌                 | ✅ `/api/research`    | `core.config`, `core.research`                           | `router`                                        | **ORPHAN**                                    |
| [programista_endpoint.py](programista_endpoint.py)     | Router               | ❌                 | ✅ `/api/code`        | `core.executor`, `core.auth`                             | `router`                                        | **ORPHAN**                                    |
| [prometheus_endpoint.py](prometheus_endpoint.py)       | Router               | ❌                 | ✅ `/metrics`         | `core.metrics`                                           | `router`                                        | **ORPHAN**                                    |
| [nlp_endpoint.py](nlp_endpoint.py)                     | Router               | ❌                 | ✅ `/api/nlp`         | `core.nlp_processor`, `core.config`                      | `router`                                        | **ORPHAN**                                    |
| [hybrid_search_endpoint.py](hybrid_search_endpoint.py) | Re-export            | ❌                 | ✅                    | `core.hybrid_search_endpoint`                            | `router`                                        | **ORPHAN**                                    |
| [hierarchical_memory.py](hierarchical_memory.py)       | Library              | ❌                 | ❌                    | `.memory`, `.helpers`                                    | klasy memory                                    | Używa relative import (.) - **ORPHAN w root** |
| [research.py](research.py)                             | Library              | ❌                 | ❌                    | `.config`, `.helpers`, `.memory`, `.llm`                 | `autonauka`, `Material`, `LearnResult`          | Używa relative import - **ORPHAN w root**     |
| [proactive_suggestions.py](proactive_suggestions.py)   | Library              | ❌                 | ❌                    | (none)                                                   | `analyze_context`, `get_smart_suggestions`      | `tests/test_vision_tts.py`                    |
| [system_stats.py](system_stats.py)                     | Library              | ❌                 | ❌                    | `core.memory`                                            | `system_stats`, `init_monitor`                  | `routers.py`                                  |
| [vision_provider.py](vision_provider.py)               | Library              | ❌                 | ❌                    | `core.config`, `core.helpers`                            | `analyze_image_universal`                       | `tests/test_vision_tts.py`                    |
| [writer_pro.py](writer_pro.py)                         | Router               | ❌                 | ✅ `/api/writer`      | `core.config`, `core.auth`, `core.writing`               | `writer_router`                                 | **ORPHAN**                                    |
| [autonauka_pro.py](autonauka_pro.py)                   | Library              | ❌                 | ❌                    | `core.config`, `core.llm`, `core.memory`                 | (funkcje autonauki)                             | **ORPHAN**                                    |
| [sports_news_pro.py](sports_news_pro.py)               | Library              | ❌                 | ❌                    | `core.config`                                            | `news_search`, `get_sports_scores`              | **ORPHAN**                                    |
| [example.py](example.py)                               | Example              | ❌                 | ❌                    | -                                                        | -                                               | **ORPHAN**                                    |

### PLIKI NARZĘDZIOWE/PATCHE (root)

| Plik                                                                                                                                 | Typ           | Entrypoint? | Cel                                  |
| ------------------------------------------------------------------------------------------------------------------------------------ | ------------- | ----------- | ------------------------------------ |
| [deploy.py](deploy.py)                                                                                                               | Deploy script | ✅ L:201    | SSH deployment do OVH                |
| [print_routes.py](print_routes.py)                                                                                                   | CLI Tool      | ✅ L:42     | Wyświetla wszystkie routes           |
| [set_memory_db_env.py](set_memory_db_env.py)                                                                                         | CLI Tool      | ✅ L:52     | Ustawia MEM_DB env                   |
| [stress_test_system.py](stress_test_system.py)                                                                                       | Test Tool     | ✅ L:498    | Stress test systemu                  |
| [ultra_destruction_test.py](ultra_destruction_test.py)                                                                               | Test Tool     | ✅ L:579    | Extreme stress test                  |
| [test_web_learn.py](test_web_learn.py)                                                                                               | Test          | ❌          | Testuje web_learn                    |
| [audit_adv_cog_extract.py](audit_adv_cog_extract.py)                                                                                 | Audit Tool    | ✅ L:207    | Audit cognitive engine               |
| [fix_conversations_tables.py](fix_conversations_tables.py)                                                                           | Fix Script    | ✅ L:271    | Fix DB tables                        |
| [fix_hier_mem_await.py](fix_hier_mem_await.py)                                                                                       | Fix Script    | ✅ L:73     | Fix hierarchical memory              |
| [fix_openai_compat_broken_strings.py](fix_openai_compat_broken_strings.py)                                                           | Fix Script    | ✅ L:88     | Fix OpenAI compat                    |
| [fix_openai_compat_boundary_hard.py](fix_openai_compat_boundary_hard.py)                                                             | Fix Script    | ✅ L:27     | Fix OpenAI boundaries                |
| [patch_add_cognitive_mode_enum.py](patch_add_cognitive_mode_enum.py)                                                                 | Patch         | ✅ L:178    | Dodaje CognitiveMode enum            |
| [patch_add_get_advanced_cognitive_engine.py](patch_add_get_advanced_cognitive_engine.py)                                             | Patch         | ✅ L:86     | Dodaje get_advanced_cognitive_engine |
| [patch_app_nonfatal_failed_routers.py](patch_app_nonfatal_failed_routers.py)                                                         | Patch         | ✅ L:87     | Nonfatal routers                     |
| [patch_bootstrap_advanced_cognitive_types.py](patch_bootstrap_advanced_cognitive_types.py)                                           | Patch         | ✅ L:122    | Bootstrap cognitive types            |
| [patch_chatbox_buffer.py](patch_chatbox_buffer.py)                                                                                   | Patch         | ✅ L:262    | Fix chatbox buffer                   |
| [patch_disable_any_router_exception_handler_router_vars.py](patch_disable_any_router_exception_handler_router_vars.py)               | Patch         | ✅ L:84     | Disable router exceptions            |
| [patch_disable_apirouter_exception_handler_repo_wide.py](patch_disable_apirouter_exception_handler_repo_wide.py)                     | Patch         | ✅ L:73     | Disable APIRouter exceptions         |
| [patch_fix_deploy_py_fstring_backslash.py](patch_fix_deploy_py_fstring_backslash.py)                                                 | Patch         | ✅ L:54     | Fix f-string backslash               |
| [patch_fix_future_import_position_in_advanced_cognitive_engine.py](patch_fix_future_import_position_in_advanced_cognitive_engine.py) | Patch         | ✅ L:85     | Fix **future** import                |
| [patch_fix_writing_fstring_resub_cat_tag.py](patch_fix_writing_fstring_resub_cat_tag.py)                                             | Patch         | ✅ L:92     | Fix writing f-string                 |
| [patch_fix_writing_hashtags_fstring_regex.py](patch_fix_writing_hashtags_fstring_regex.py)                                           | Patch         | ✅ L:60     | Fix hashtags regex                   |
| [patch_force_alias_get_advanced_cognitive_engine.py](patch_force_alias_get_advanced_cognitive_engine.py)                             | Patch         | ✅ L:59     | Force engine alias                   |
| [patch_move_cognitive_mode_to_top.py](patch_move_cognitive_mode_to_top.py)                                                           | Patch         | ✅ L:198    | Move CognitiveMode                   |
| [patch_mrd_fix_compile_and_failed_routers.py](patch_mrd_fix_compile_and_failed_routers.py)                                           | Patch         | ✅ L:429    | Fix compile errors                   |
| [patch_mrd_fix_fstrings_and_router_exception_handler.py](patch_mrd_fix_fstrings_and_router_exception_handler.py)                     | Patch         | ✅ L:104    | Fix f-strings                        |
| [patch_nonfatal_failed_routers_everywhere.py](patch_nonfatal_failed_routers_everywhere.py)                                           | Patch         | ✅ L:123    | Nonfatal routers everywhere          |
| [patch_stream_finaldelta.py](patch_stream_finaldelta.py)                                                                             | Patch         | ✅ L:264    | Fix streaming delta                  |
| [patch_stream_pingflush.py](patch_stream_pingflush.py)                                                                               | Patch         | ✅ L:310    | Fix stream ping flush                |
| [tools_fix_hybrid_primary.py](tools_fix_hybrid_primary.py)                                                                           | Tool          | ✅ L:254    | Fix hybrid primary                   |
| [tools_fix_hybrid_primary_v2.py](tools_fix_hybrid_primary_v2.py)                                                                     | Tool          | ✅ L:300    | Fix hybrid v2                        |
| [tools_fix_hybrid_router.py](tools_fix_hybrid_router.py)                                                                             | Tool          | ✅ L:242    | Fix hybrid router                    |
| [tools_patch_app_aliases.py](tools_patch_app_aliases.py)                                                                             | Tool          | ✅ L:116    | Patch app aliases                    |
| [tools_patch_app_get_automation_summary.py](tools_patch_app_get_automation_summary.py)                                               | Tool          | ✅ L:65     | Patch automation summary             |
| [tools_patch_app_get_automation_summary_refresh.py](tools_patch_app_get_automation_summary_refresh.py)                               | Tool          | ✅ L:80     | Refresh automation summary           |
| [tools_patch_hybrid_call_helper.py](tools_patch_hybrid_call_helper.py)                                                               | Tool          | ✅ L:119    | Hybrid call helper                   |
| [tools_patch_hybrid_callsite.py](tools_patch_hybrid_callsite.py)                                                                     | Tool          | ✅ L:144    | Hybrid callsite                      |

---

### 2️⃣ PLIKI CORE (`mrd/core/`)

#### Rdzeń systemu (zawsze używane)

| Plik                            | Typ           | Entrypoint? | Router? | Główne eksporty                                                 | Importowany przez                         |
| ------------------------------- | ------------- | ----------- | ------- | --------------------------------------------------------------- | ----------------------------------------- |
| [**init**.py](core/__init__.py) | Package init  | ❌          | ❌      | `__version__`, `lazy_import`                                    | Wszystko w core                           |
| [config.py](core/config.py)     | Config        | ❌          | ❌      | `AUTH_TOKEN`, `DB_PATH`, `LLM_*`, stałe                         | Prawie wszystko                           |
| [auth.py](core/auth.py)         | Auth          | ❌          | ❌      | `check_auth`, `auth_dependency`, `verify_token`                 | Wszystkie endpointy                       |
| [helpers.py](core/helpers.py)   | Utilities     | ❌          | ❌      | `log_*`, `http_*`, `tokenize`, `make_id`, `embed_*`, `cosine_*` | Prawie wszystko                           |
| [llm.py](core/llm.py)           | LLM Client    | ❌          | ❌      | `call_llm`, `call_llm_raw`, `call_llm_stream`, `get_llm_client` | cognitive_engine, research, writing, itp. |
| [memory.py](core/memory.py)     | Memory System | ❌          | ❌      | `memory_manager`, `stm_*`, `ltm_*`, `psy_*`, `_db`, `_init_db`  | Prawie wszystko                           |
| [prompt.py](core/prompt.py)     | Prompt Config | ❌          | ❌      | `SYSTEM_PROMPT`                                                 | config.py, cognitive_engine               |

#### Systemy kognitywne

| Plik                                                              | Typ         | Entrypoint? | Router? | Główne eksporty                                                                                            | Importowany przez                    |
| ----------------------------------------------------------------- | ----------- | ----------- | ------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| [cognitive_engine.py](core/cognitive_engine.py)                   | Engine      | ❌          | ❌      | `CognitiveEngine`, `cognitive_engine`                                                                      | assistant_endpoint.py                |
| [advanced_cognitive_engine.py](core/advanced_cognitive_engine.py) | Engine      | ❌          | ❌      | `CognitiveMode`, `CognitiveResult`, `AdvancedCognitiveEngine`, `get_engine`, `process_with_full_cognition` | cognitive_engine, cognitive_endpoint |
| [hierarchical_memory.py](core/hierarchical_memory.py)             | Memory      | ❌          | ❌      | `HierarchicalMemorySystem`, `get_hierarchical_memory`, klasy L1-L4                                         | cognitive_engine, tests              |
| [advanced_memory.py](core/advanced_memory.py)                     | Memory      | ❌          | ❌      | `MemoryNode`, funkcje LTM                                                                                  | cognitive_engine                     |
| [advanced_psychology.py](core/advanced_psychology.py)             | Psychology  | ❌          | ❌      | `get_psyche_state`, `process_user_message`, `EmotionalState`                                               | psyche_endpoint, advanced_proactive  |
| [advanced_proactive.py](core/advanced_proactive.py)               | Suggestions | ❌          | ❌      | `get_proactive_suggestions`, `ConversationAnalyzer`                                                        | suggestions_endpoint                 |
| [advanced_learning.py](core/advanced_learning.py)                 | Learning    | ❌          | ❌      | `AdvancedLearningManager`                                                                                  | **ORPHAN**                           |
| [advanced_autorouter.py](core/advanced_autorouter.py)             | Router      | ❌          | ❌      | `AdvancedAutoRouter`, `AutoRouteResult`                                                                    | **ORPHAN**                           |
| [advanced_llm.py](core/advanced_llm.py)                           | LLM         | ❌          | ❌      | `call_advanced_llm`, `adaptive_llm_call`                                                                   | **ORPHAN** (używa core.llm)          |

#### Systemy specjalistyczne

| Plik                                                            | Typ             | Entrypoint? | Router? | Główne eksporty                                         | Importowany przez                       |
| --------------------------------------------------------------- | --------------- | ----------- | ------- | ------------------------------------------------------- | --------------------------------------- |
| [research.py](core/research.py)                                 | Web Research    | ❌          | ❌      | `autonauka`, `travel_search`, `web_learn`               | research_endpoint, cognitive_engine     |
| [writing.py](core/writing.py)                                   | Content Gen     | ❌          | ❌      | `creative_writing`, `vinted_desc`, `auction_desc`       | writing_endpoint                        |
| [semantic.py](core/semantic.py)                                 | NLP Analysis    | ❌          | ❌      | `SemanticAnalyzer`, `semantic_analyze`, `embed_text`    | advanced_proactive, cognitive_endpoint  |
| [tools.py](core/tools.py)                                       | Internet Tools  | ❌          | ❌      | `InternetSearcher`, news/sports funkcje                 | cognitive_engine                        |
| [tools_registry.py](core/tools_registry.py)                     | Tools Registry  | ✅ L:991    | ❌      | `TOOLS_REGISTRY`, `get_all_tools`, `get_tool_by_name`   | cognitive_engine, app                   |
| [executor.py](core/executor.py)                                 | Code Executor   | ❌          | ❌      | `Programista`, `ExecResult`                             | programista_endpoint                    |
| [nlp_processor.py](core/nlp_processor.py)                       | NLP SpaCy       | ✅ L:554    | ❌      | `NLPProcessor`, `get_nlp_processor`                     | nlp_endpoint, cognitive_endpoint        |
| [self_reflection.py](core/self_reflection.py)                   | Self-Reflection | ✅ L:691    | ❌      | `SelfReflectionEngine`, `reflect_on_response`           | reflection_endpoint, cognitive_endpoint |
| [inner_language.py](core/inner_language.py)                     | Inner Language  | ✅ L:1341   | ❌      | `InnerLanguageProcessor`, `InnerToken`                  | **ORPHAN**                              |
| [multi_agent_orchestrator.py](core/multi_agent_orchestrator.py) | Multi-Agent     | ✅ L:1056   | ❌      | `MultiAgentOrchestrator`, `AgentRole`                   | **ORPHAN**                              |
| [user_model.py](core/user_model.py)                             | User Profile    | ❌          | ❌      | `UserModel`, `user_model_manager`                       | advanced_proactive                      |
| [sessions.py](core/sessions.py)                                 | Sessions DB     | ❌          | ❌      | `ConnectionPool`, session management                    | assistant_simple                        |
| [context_awareness.py](core/context_awareness.py)               | Context         | ❌          | ❌      | `calculate_message_importance`, compression             | **ORPHAN**                              |
| [smart_context.py](core/smart_context.py)                       | Smart Context   | ❌          | ❌      | `ScoredMessage`, TF-IDF scoring                         | **ORPHAN**                              |
| [knowledge_compression.py](core/knowledge_compression.py)       | Compression     | ❌          | ❌      | `KnowledgeCompressor`                                   | **ORPHAN**                              |
| [intent_dispatcher.py](core/intent_dispatcher.py)               | Intent          | ❌          | ❌      | `FAST_PATH_HANDLERS`, `analyze_intent_and_select_tools` | cognitive_engine                        |
| [future_predictor.py](core/future_predictor.py)                 | Prediction      | ❌          | ❌      | `FutureContextPredictor`                                | **ORPHAN**                              |
| [fact_validation.py](core/fact_validation.py)                   | Validation      | ❌          | ❌      | `FactValidator`, `validate_facts`                       | **ORPHAN**                              |
| [conversation_analytics.py](core/conversation_analytics.py)     | Analytics       | ❌          | ❌      | `ConversationAnalytics`                                 | **ORPHAN**                              |
| [ai_auction.py](core/ai_auction.py)                             | Auctions        | ❌          | ❌      | `AIAuctionManager`                                      | auction_endpoint                        |
| [autoroute.py](core/autoroute.py)                               | Auto-route      | ❌          | ❌      | `decide`, `AutoRouteDecision`                           | **ORPHAN**                              |
| [brave_search.py](core/brave_search.py)                         | Brave Search    | ✅ L:243    | ❌      | `brave_web_search`, `BraveResult`                       | **ORPHAN**                              |
| [tavily_search.py](core/tavily_search.py)                       | Tavily Search   | ✅ L:159    | ❌      | `tavily_search`, `TavilyResult`                         | **ORPHAN**                              |

#### Memory/Storage

| Plik                                                | Typ         | Entrypoint? | Router?          | Główne eksporty                          | Importowany przez |
| --------------------------------------------------- | ----------- | ----------- | ---------------- | ---------------------------------------- | ----------------- |
| [memory_store.py](core/memory_store.py)             | Memory DB   | ❌          | ❌               | `add_memory`, `search_memory`, `init_db` | memory_endpoint   |
| [memory_endpoint.py](core/memory_endpoint.py)       | Router      | ❌          | ✅ `/api/memory` | `router`                                 | app.py (core)     |
| [memory_summarizer.py](core/memory_summarizer.py)   | Summarizer  | ❌          | ❌               | `summarize_text`, `summarize_session`    | **ORPHAN**        |
| [memory_persistence.py](core/memory_persistence.py) | Persistence | ❌          | ❌               | `MemoryBackupManager`                    | **ORPHAN**        |

#### Batch/Parallel

| Plik                                            | Typ      | Entrypoint? | Router?         | Główne eksporty                  | Importowany przez |
| ----------------------------------------------- | -------- | ----------- | --------------- | -------------------------------- | ----------------- |
| [batch_processing.py](core/batch_processing.py) | Batch    | ✅ L:535    | ❌              | `BatchProcessor`, `BatchRequest` | batch_endpoint    |
| [batch_endpoint.py](core/batch_endpoint.py)     | Router   | ❌          | ✅ `/api/batch` | `router`                         | app.py            |
| [parallel.py](core/parallel.py)                 | Parallel | ❌          | ❌              | `AsyncTaskPool`, `parallel_map`  | advanced_memory   |

#### Infrastructure

| Plik                                            | Typ        | Entrypoint? | Router? | Główne eksporty                    | Importowany przez |
| ----------------------------------------------- | ---------- | ----------- | ------- | ---------------------------------- | ----------------- |
| [metrics.py](core/metrics.py)                   | Prometheus | ❌          | ❌      | `record_*`, `PROMETHEUS_AVAILABLE` | app, middleware   |
| [middleware.py](core/middleware.py)             | Middleware | ❌          | ❌      | `SimpleCache`, `CacheStats`        | **ORPHAN**        |
| [redis_middleware.py](core/redis_middleware.py) | Redis      | ❌          | ❌      | `RedisCache`, `get_redis`          | memory, llm       |
| [response_adapter.py](core/response_adapter.py) | Adapter    | ❌          | ❌      | `adapt`                            | memory_endpoint   |

#### Endpointy w core

| Plik                                                        | Typ                 | Entrypoint?            | Router?     | Prefix                | Importowany przez            |
| ----------------------------------------------------------- | ------------------- | ---------------------- | ----------- | --------------------- | ---------------------------- |
| [app.py](core/app.py)                                       | **MAIN ENTRYPOINT** | ✅ L:623 `uvicorn.run` | FastAPI app | `/`                   | **Alternatywny entrypoint**  |
| [assistant_endpoint.py](core/assistant_endpoint.py)         | Router              | ❌                     | ✅          | `/api/chat`           | app.py (via core modules)    |
| [admin_endpoint.py](core/admin_endpoint.py)                 | Router              | ❌                     | ✅          | `/api/admin`          | **ORPHAN**                   |
| [auction_endpoint.py](core/auction_endpoint.py)             | Router              | ❌                     | ✅          | `/api/auction`        | **ORPHAN**                   |
| [batch_endpoint.py](core/batch_endpoint.py)                 | Router              | ❌                     | ✅          | `/api/batch`          | app.py                       |
| [chat_advanced_endpoint.py](core/chat_advanced_endpoint.py) | Router              | ❌                     | ✅          | `/core/chat/advanced` | **ORPHAN**                   |
| [cognitive_endpoint.py](core/cognitive_endpoint.py)         | Router              | ❌                     | ✅          | `/api/cognitive`      | app.py                       |
| [hacker_endpoint.py](core/hacker_endpoint.py)               | Router              | ❌                     | ✅          | `/api/hacker`         | **ORPHAN**                   |
| [hybrid_search_endpoint.py](core/hybrid_search_endpoint.py) | Router              | ❌                     | ✅          | `/api/search`         | app.py                       |
| [legal_office_endpoint.py](core/legal_office_endpoint.py)   | Router              | ❌                     | ✅          | `/api/legal`          | app.py                       |
| [memory_endpoint.py](core/memory_endpoint.py)               | Router              | ❌                     | ✅          | `/api/memory`         | app.py                       |
| [negocjator_endpoint.py](core/negocjator_endpoint.py)       | Router              | ❌                     | ✅          | `/api/negocjator`     | app.py                       |
| [prometheus_endpoint.py](core/prometheus_endpoint.py)       | Router              | ❌                     | ✅          | `/metrics`            | app.py                       |
| [psyche_endpoint.py](core/psyche_endpoint.py)               | Router              | ❌                     | ✅          | `/api/psyche`         | **ORPHAN** (duplikat w root) |
| [reflection_endpoint.py](core/reflection_endpoint.py)       | Router              | ❌                     | ✅          | `/api/reflection`     | app.py                       |
| [research_endpoint.py](core/research_endpoint.py)           | Router              | ❌                     | ✅          | `/api/research`       | **ORPHAN** (duplikat w root) |
| [suggestions_endpoint.py](core/suggestions_endpoint.py)     | Router              | ❌                     | ✅          | `/api/suggestions`    | **ORPHAN**                   |

#### Testy i narzędzia w core

| Plik                                                        | Typ  | Entrypoint? |
| ----------------------------------------------------------- | ---- | ----------- |
| [stress_test_system.py](core/stress_test_system.py)         | Test | ✅ L:498    |
| [ultra_destruction_test.py](core/ultra_destruction_test.py) | Test | ✅ L:579    |

---

### 3️⃣ TESTY (`mrd/tests/`)

| Plik                                                                 | Typ               | Główne testy                                                           |
| -------------------------------------------------------------------- | ----------------- | ---------------------------------------------------------------------- |
| [**init**.py](tests/__init__.py)                                     | Package           | -                                                                      |
| [conftest.py](tests/conftest.py)                                     | Pytest fixtures   | `client`, `auth_headers`, `test_message`                               |
| [test_api_endpoints.py](tests/test_api_endpoints.py)                 | API Tests         | Chat, TTS, Psyche, Travel, Files, Admin, Prometheus                    |
| [test_batch_processing.py](tests/test_batch_processing.py)           | Batch Tests       | BatchProcessor                                                         |
| [test_core_modules.py](tests/test_core_modules.py)                   | Core Tests        | config, auth, helpers, memory, llm, semantic, research, tools, writing |
| [test_hierarchical_memory.py](tests/test_hierarchical_memory.py)     | Memory Tests      | Episodic, Semantic, Procedural                                         |
| [test_integration.py](tests/test_integration.py)                     | Integration       | ChatFlow, VisionFlow, TTSFlow, MemoryPersistence, ErrorHandling        |
| [test_proactive_suggestions.py](tests/test_proactive_suggestions.py) | Suggestions Tests | ✅ L:104                                                               |
| [test_vision_tts.py](tests/test_vision_tts.py)                       | Vision/TTS Tests  | VisionProvider, TTSProvider                                            |
| [test_writing_endpoint.py](tests/test_writing_endpoint.py)           | Writing Tests     | creative, vinted, social, fashion                                      |

---

### 4️⃣ SCRIPTS I TOOLS

| Plik                                                           | Typ    | Entrypoint? | Cel                                     |
| -------------------------------------------------------------- | ------ | ----------- | --------------------------------------- |
| [scripts/check_requirements.py](scripts/check_requirements.py) | Script | ❌          | Sprawdza zależności vs requirements.txt |
| [tools/mrd_repo_index.py](tools/mrd_repo_index.py)             | Tool   | ✅ L:302    | Generuje index repo (MRD_INDEX.json)    |
| [tools/patch_hybrid_pick.py](tools/patch_hybrid_pick.py)       | Tool   | ✅ L:152    | Patchuje \_pick_hybrid_callable         |

---

## 🚀 LISTA WSZYSTKICH ENTRYPOINTÓW

Pliki z `if __name__ == "__main__"` lub `uvicorn.run`:

| #     | Plik                                | Linia                       | Typ                           |
| ----- | ----------------------------------- | --------------------------- | ----------------------------- |
| 1     | **core/app.py**                     | L:623 + L:639 (uvicorn.run) | **GŁÓWNY SERWER PRODUKCYJNY** |
| 2     | deploy.py                           | L:201                       | Deploy script SSH             |
| 3     | print_routes.py                     | L:42                        | CLI - lista routes            |
| 4     | set_memory_db_env.py                | L:52                        | CLI - ustawia MEM_DB          |
| 5     | stress_test_system.py               | L:498                       | Stress test                   |
| 6     | ultra_destruction_test.py           | L:579                       | Extreme test                  |
| 7     | audit_adv_cog_extract.py            | L:207                       | Audit tool                    |
| 8     | fix_conversations_tables.py         | L:271                       | DB fix                        |
| 9     | fix_hier_mem_await.py               | L:73                        | Memory fix                    |
| 10    | fix_openai_compat_broken_strings.py | L:88                        | Fix strings                   |
| 11    | fix_openai_compat_boundary_hard.py  | L:27                        | Fix boundaries                |
| 12-30 | patch\_\*.py (18 plików)            | różne                       | Patche                        |
| 31-38 | tools\_\*.py (8 plików w root)      | różne                       | Narzędzia                     |
| 39    | tools/mrd_repo_index.py             | L:302                       | Repo indexer                  |
| 40    | tools/patch_hybrid_pick.py          | L:152                       | Hybrid patch                  |
| 41    | core/batch_processing.py            | L:535                       | Batch test                    |
| 42    | core/brave_search.py                | L:243                       | Brave test                    |
| 43    | core/inner_language.py              | L:1341                      | Inner language test           |
| 44    | core/multi_agent_orchestrator.py    | L:1056                      | Multi-agent test              |
| 45    | core/nlp_processor.py               | L:554                       | NLP test                      |
| 46    | core/self_reflection.py             | L:691                       | Reflection test               |
| 47    | core/stress_test_system.py          | L:498                       | Stress test (duplikat)        |
| 48    | core/tavily_search.py               | L:159                       | Tavily test                   |
| 49    | core/tools_registry.py              | L:991                       | Tools registry test           |
| 50    | core/ultra_destruction_test.py      | L:579                       | Ultra test (duplikat)         |
| 51    | tests/test_proactive_suggestions.py | L:104                       | Pytest entry                  |

---

## 🔴 ORPHAN FILES (NIGDZIE NIE IMPORTOWANE)

Pliki które nie są importowane z żadnego innego pliku w projekcie:

### Krytyczne orphany (powinny być używane):

1. **assistant_endpoint.py** (root) - duplikat? nie używany w app.py
2. **writing_endpoint.py** - nie w liście routerów app.py
3. **psyche_endpoint.py** (root) - duplikat core/psyche_endpoint.py
4. **travel_endpoint.py** - nie w liście routerów
5. **research_endpoint.py** (root) - duplikat core/
6. **programista_endpoint.py** - nie w liście routerów
7. **prometheus_endpoint.py** (root) - duplikat core/
8. **nlp_endpoint.py** - nie w liście routerów
9. **hybrid_search_endpoint.py** (root) - tylko re-export
10. **writer_pro.py** - router nie używany

### Zaawansowane moduły orphany:

11. **core/advanced_learning.py** - nie importowany
12. **core/advanced_autorouter.py** - nie importowany
13. **core/advanced_llm.py** - nie importowany (odsyła do core.llm)
14. **core/inner_language.py** - nie importowany
15. **core/multi_agent_orchestrator.py** - nie importowany
16. **core/context_awareness.py** - nie importowany
17. **core/smart_context.py** - nie importowany
18. **core/knowledge_compression.py** - nie importowany
19. **core/future_predictor.py** - nie importowany
20. **core/fact_validation.py** - nie importowany
21. **core/conversation_analytics.py** - nie importowany
22. **core/autoroute.py** - nie importowany
23. **core/brave_search.py** - nie importowany (jest tavily)
24. **core/tavily_search.py** - nie importowany
25. **core/memory_summarizer.py** - nie importowany
26. **core/memory_persistence.py** - nie importowany
27. **core/middleware.py** - nie importowany (jest redis_middleware)

### Duplikaty root/core:

28. **hierarchical_memory.py** (root) - używa relative import "." - nie działa w root
29. **research.py** (root) - używa relative import "." - nie działa w root

### Endpointy orphany w core:

30. **core/admin_endpoint.py** - nie w liście app.py
31. **core/auction_endpoint.py** - nie w liście
32. **core/chat_advanced_endpoint.py** - nie w liście
33. **core/hacker_endpoint.py** - nie w liście
34. **core/suggestions_endpoint.py** - nie w liście (używa advanced_proactive bezpośrednio)

---

## 📈 GRAF ZALEŻNOŚCI (KLUCZOWE MODUŁY)

```
app.py (root)
├── openai_compat.router
├── assistant_simple.router
├── routers.router
├── stt_endpoint.router
├── tts_endpoint.router
├── suggestions_endpoint.router
├── internal_endpoint.router
├── files_endpoint.router
└── core.*_endpoint.router (9 modułów)

core/app.py (alternatywny entrypoint)
├── core.metrics
├── core.memory
└── (wiele routerów bezpośrednio)

core/cognitive_engine.py
├── core.config
├── core.llm
├── core.memory
├── core.hierarchical_memory
├── core.advanced_cognitive_engine
├── core.intent_dispatcher
├── core.research (opcjonalnie)
├── core.user_model (opcjonalnie)
└── core.tools_registry

core/memory.py
├── core.config
├── core.helpers
└── core.redis_middleware (opcjonalnie)

core/llm.py
├── core.config
├── core.helpers
└── core.redis_middleware (opcjonalnie)
```

---

## ✅ REKOMENDACJE

### 1. Usunąć duplikaty root/core:

- `research.py`, `hierarchical_memory.py` w root używają relative imports i nie działają
- Wiele `*_endpoint.py` ma duplikaty w root i core

### 2. Podłączyć brakujące routery do app.py:

- writing_endpoint, travel_endpoint, programista_endpoint, nlp_endpoint, writer_pro

### 3. Zintegrować orphan moduły zaawansowane:

- advanced_learning, advanced_autorouter, inner_language, multi_agent_orchestrator
- brave_search, tavily_search (jako alternatywy dla SERPAPI)
- fact_validation, conversation_analytics, future_predictor

### 4. Oczyścić pliki patch/fix:

- 35+ plików patch*\*.py i fix*\*.py - większość jednorazowych fix'ów
- Można przenieść do folderu `archive/` lub usunąć

### 5. Zunifikować entrypoint:

- `app.py` (root) vs `core/app.py` - różne konfiguracje routerów
- Rozważyć jeden główny entrypoint

---

**Koniec raportu audytowego**
