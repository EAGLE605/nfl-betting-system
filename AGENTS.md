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
- **Tests**: `pytest tests/ -v` (63 tests)
- **Type check**: `mypy src/ --ignore-missing-imports --no-strict-optional`

Line length is standardized to **88** (matching Black's default) across `pyproject.toml`, `.pre-commit-config.yaml`, and ruff config.

### Gotchas discovered during setup

- Scripts in `/home/ubuntu/.local/bin` (pytest, ruff, black, streamlit, etc.) require `$HOME/.local/bin` on `PATH`. The update script ensures this.
- External API keys (`ODDS_API_KEY`, `XAI_API_KEY`, etc.) are optional for running tests and the dashboard UI. They are only needed for live odds data and AI-powered analysis features.
- `dashboard/app.py` imports from `src/` using `sys.path` manipulation. Always run from the repo root (`/workspace`).
- Admin credentials for the auth system are loaded from environment variables (`NFL_ADMIN_EMAIL`, `NFL_ADMIN_USERNAME`, `NFL_ADMIN_PASSWORD`); they are **not** hardcoded.
- `ModelCalibrator` uses sklearn's `CalibratedClassifierCV` — the `cv="prefit"` parameter was removed in sklearn 1.8; the implementation handles this automatically.
- `BacktestEngine.run_monte_carlo()` provides bootstrap confidence intervals; the validation swarm's `_stress_testing` uses this for strategy approval.
- Two env file conventions coexist: `settings.py`/`secrets.py` load root `.env`, while dashboard/scripts load `config/api_keys.env`. Prefer root `.env` for new code.
