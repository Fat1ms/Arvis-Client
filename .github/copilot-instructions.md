# Arvis AI Assistant · Copilot Guide

## 🚧 Cu## Pitfalls & Quick Fixes
- Load `vosk-model-small-ru-0.22` for wake word detection to avoid multi-minute initialization; reserve the full model for full STT.
- Replace `localhost` with `127.0.0.1` in any new networking code to prevent IPv6 stalls (FastHTTP already does this—follow its pattern).
- Keep TTS work off the UI thread; fallback lives in `modules/tts_worker_subprocess.py` for long operations.
- Audit logs in `logs/audit/*.jsonl` rotate at 10 MB with 90-day TTL—respect this when extending logging.
- Packaging uses PyInstaller (`build_exe.bat`); ship the resulting `dist/` folder together with `models/`, `config/`, and `UXUI/` assets.
- **Server Code**: Currently in production—avoid breaking changes; test thoroughly on local setup before suggesting server modifications.

## Testing Phase Best Practices
- **Run tests before commits**: `pytest tests/` must pass
- **No experimental server changes**: Stick to client-side improvements and bug fixes
- **Document all changes**: Update CHANGELOG.md and relevant docs
- **Incremental improvements**: Small, testable changes over large refactors
- **Backwards compatibility**: Maintain compatibility with existing user configs and dataDevelopment Phase
**STATUS: Testing & Stabilization**
- **NO CRITICAL CHANGES** to server code (`server/`) without explicit approval
- Focus on testing, bug fixes, and documentation improvements
- New feature in development: **Auto-Update System** for Arvis client

## Overview
- Desktop voice assistant built with PyQt5; offline Vosk STT/TTS, Ollama LLM, RBAC & 2FA security.
- Entry `main.py` loads frameless `MainWindow` from `src/gui/`; core dialog engine lives in `src/core/arvis_core.py`.
- Feature modules in `modules/` (weather, news, calendar, system control, search) run before the LLM; plug-ins follow this routing.

## Key Flows
- `ArvisCore.process_message` → `handle_module_commands` chain → `LLMClient.stream_response` if nothing matches.
- TTS streaming buffers via `_stream_buffer_text`; send chunks ≥20 chars to `modules/tts_engine.py`, flush with `TTSEngine.flush_buffer()`.
- Conversation history persists every 5 turns to `data/conversation_history.json` and trims to 50 entries.

## Patterns & Conventions
- Keep the Qt UI thread free: heavy tasks go through `utils.async_manager.AsyncTaskManager.run_async`, results surfaced with signals (`response_ready`, `status_changed`, etc.).
- Localize all UI strings using `_()` from `i18n/I18N`; after changes call `apply_to_widget_tree` to refresh widgets.
- Enforce permissions with `utils/security/rbac.py` helpers or `@require_permission`; admin user is immutable, guests are chat-only with 30‑minute sessions.
- Configuration merges `config/config.json` + `.env` via `config/config.py`; secrets stay in `.env`, wake words set at `stt.kaldi_wake_words`.
- Use `utils/fast_http.FastHTTPClient` for Ollama/HTTP calls (forces 127.0.0.1, has caching); `modules/llm_client.py` auto-picks an available model when `default_model="auto"`.

## Developer Workflows
- Python 3.11/3.12 only (PyAudio fails on 3.13). Run `setup_arvis.bat` once, then `start_arvis.bat`; `start_arvis_simple.bat` skips the Ollama availability check.
- Manual launch: activate venv → `python main.py`. Health checks and troubleshooting use `status_check.bat`, `diagnose_setup.bat`, `diagnose_performance.bat`; control Ollama through `ollama_manager.bat`.
- Tests: unit coverage via `pytest` (add files under `tests/`), voice integration probe with `python tests\debug_test.py`. When adding modules, register them in `ArvisCore.__init__` and extend `handle_module_commands` plus RBAC permissions.
- **Testing Phase Protocol**: All changes must pass existing tests before commit; server modifications require review; prioritize stability over new features.

## Auto-Update System (In Development)
- **Goal**: Seamless client updates from GitHub releases without manual reinstallation.
- **Architecture**: Version checker (`utils/update_checker.py`) → download handler → backup system → apply updates → restart.
- **Requirements**: 
  - Check `version.py` against GitHub API releases
  - Download & verify release assets (checksums/signatures)
  - Rollback mechanism if update fails
  - User notification & consent before applying
  - Preserve user data (`data/`, `config/`, `logs/`)
- **Integration Points**: 
  - Background check on startup (non-blocking)
  - Manual check via UI menu or voice command
  - Respect `config.json` setting `auto_update.enabled`
- **Security**: Verify GitHub release authenticity; use HTTPS only; validate file integrity before extraction.

## Pitfalls & Quick Fixes
- Load `vosk-model-small-ru-0.22` for wake word detection to avoid multi-minute initialization; reserve the full model for full STT.
- Replace `localhost` with `127.0.0.1` in any new networking code to prevent IPv6 stalls (FastHTTP already does this—follow its pattern).
- Keep TTS work off the UI thread; fallback lives in `modules/tts_worker_subprocess.py` for long operations.
- Audit logs in `logs/audit/*.jsonl` rotate at 10 MB with 90-day TTL—respect this when extending logging.
- Packaging uses PyInstaller (`build_exe.bat`); ship the resulting `dist/` folder together with `models/`, `config/`, and `UXUI/` assets.
