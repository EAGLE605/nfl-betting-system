# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

NFL Betting System — a Python monolith (no Docker, no external DB) using XGBoost/LightGBM for NFL game prediction, Streamlit for the dashboard UI, and embedded SQLite for data storage.

### Running services

| Service | Command | URL |
|---|---|---|
| **Streamlit Dashboard** | `streamlit run dashboard/app.py --server.port 8501 --server.headless true` | `http://localhost:8501` |

The dashboard is the primary UI. There is no separate backend service to start — all logic runs in-process via Streamlit.

### Lint / Test / Build

Standard commands are documented in the `Makefile` and `README.md`. Quick reference:

- **Lint**: `ruff check src/ scripts/ tests/` and `black --check src/ scripts/ tests/`
- **Tests**: `pytest tests/ -v` (33 tests, all pass)
- **Type check**: `mypy src/ --ignore-missing-imports --no-strict-optional`

### Gotchas discovered during setup

- `pytz` is required at runtime by the dashboard but is **not** listed in `requirements.txt`. The update script installs it explicitly.
- Scripts in `/home/ubuntu/.local/bin` (pytest, ruff, black, streamlit, etc.) require `$HOME/.local/bin` on `PATH`. The update script adds this to `~/.bashrc` if not already present.
- The codebase has ~78 pre-existing `ruff` warnings and 3 files needing `black` formatting. These are not regressions — they exist on `master`.
- External API keys (`ODDS_API_KEY`, `XAI_API_KEY`, etc.) are optional for running tests and the dashboard UI. They are only needed for live odds data and AI-powered analysis features.
- `dashboard/app.py` imports from `src/` using `sys.path` manipulation. Always run from the repo root (`/workspace`).
