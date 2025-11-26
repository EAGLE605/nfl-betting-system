# NFL Betting System - Claude Code Project Instructions

## Project Overview

**System**: Production-grade NFL betting system with machine learning predictions, real-time odds tracking, and automated strategy discovery.

**Tech Stack**: Python 3.11+, XGBoost, Streamlit, SQLite, nflfastR data pipeline

**Philosophy**: Production reliability over research experiments. Every feature must be tested, verified, and bulletproof.

---

## CRITICAL: Verification Requirements

**⚠️ NEVER claim a task is complete without verification and proof.**

After implementing ANY feature, you MUST automatically:

### 1. Show File Changes
# List created/modified files with timestamps
ls -la src/new_file.py
dir data\strategies\registry.json  # Windows

### 2. Display Contents
# Show critical file contents (configs, registries, databases)
cat data/strategies/registry.json
type config.yaml  # Windows
python -c "import json; print(json.dumps(json.load(open('file.json')), indent=2))"

### 3. Execute and Verify
# Run the code and show output
python script.py
python -m pytest tests/test_feature.py -v
python -m src.health.health_check

### 4. Test Edge Cases
- What happens if file doesn't exist?
- What happens on second run?
- What happens with invalid input?
- What happens when API fails?

### 5. Prove It Works
**Don't just say "Complete ✅". Show:**
- Before/after state comparison
- Test output (passing tests)
- Actual execution results
- Error handling in action

---

## Testing Protocol by Component

### Database Changes
# Verify table exists
python -c "import sqlite3; conn = sqlite3.connect('data/adaptive_learning.db'); print(conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall())"

# Check row count
python -c "import sqlite3; print(sqlite3.connect('data/db.db').execute('SELECT COUNT(*) FROM table_name').fetchone())"

# Show sample data
python -c "import sqlite3; import pandas as pd; print(pd.read_sql('SELECT * FROM table LIMIT 5', sqlite3.connect('data/db.db')))"

### JSON Files (Registry, Config)
# Validate and pretty-print
python -c "import json; data = json.load(open('file.json')); print(json.dumps(data, indent=2))"

# Check specific keys
python -c "import json; data = json.load(open('data/strategies/registry.json')); print(f'Strategies: {len(data)}')"

### Scripts and Pipelines
# Dry run first
python script.py --dry-run

# Full execution with verbose output
python script.py --verbose

# Run twice to test idempotency
python script.py && python script.py

### APIs and External Services
# Check circuit breaker status
python -c "from src.utils.resilience import get_circuit_status; print(get_circuit_status())"

# Test health endpoints
python -m src.health.health_check --json
curl http://localhost:8080/health  # If server running

---

## Project Structure Reference

nfl-betting-system/
├── .claude/
│   └── claude.md                  # This file - project instructions
├── data/
│   ├── strategies/
│   │   └── registry.json          # Strategy accept/reject tracking
│   ├── adaptive_learning.db       # Main prediction database
│   ├── odds_history.db            # Historical odds tracking
│   └── backups/                   # Automated database backups
├── src/
│   ├── config/
│   │   └── settings.py            # SINGLE source of truth for all config
│   ├── utils/
│   │   └── resilience.py          # Circuit breakers, retries, rate limiting
│   ├── health/
│   │   └── health_check.py        # System health monitoring
│   ├── api/
│   │   └── espn_client.py         # ESPN API with resilience
│   └── models/                    # XGBoost and prediction models
├── scripts/
│   ├── backup_database.py         # Automated SQLite backups
│   └── discover_strategies.py     # Strategy discovery engine
├── dashboard/
│   └── app.py                     # Streamlit dashboard (main interface)
└── tests/                         # Pytest test suite

---

## Common Pitfalls to AVOID

### ❌ Anti-Pattern: Claiming Without Proof
BAD:  "I created the registry.json file ✅"
GOOD: "Registry created. Contents: [shows JSON]. Test run: [shows output]"

### ❌ Anti-Pattern: Untested Code
BAD:  "The filter function will remove duplicates"
GOOD: "Filter tested with duplicate data: [shows before/after counts]"

### ❌ Anti-Pattern: Assumed State
BAD:  "The database should have the new table now"
GOOD: "Database verified: [runs query showing table exists with N rows]"

### ❌ Anti-Pattern: Silent Failures
BAD:  "Updated config file" (but didn't check if it's valid YAML)
GOOD: "Config updated and validated: [shows parsed config dict]"

---

## Standard Operating Procedures

### Adding New Features
1. Write the code
2. Write tests FIRST (test-driven)
3. Run tests and show output
4. Update health checks if applicable
5. Update this document if architecture changes
6. Run full test suite: `python -m pytest`
7. Commit with clear message

### Modifying Existing Code
1. Show current state (before)
2. Make changes
3. Show new state (after)
4. Run affected tests
5. Verify no regressions: `python -m pytest tests/`
6. Check health status: `python -m src.health.health_check`

### Database Migrations
1. Backup first: `python scripts/backup_database.py --verify`
2. Run migration script
3. Verify schema: `sqlite3 data/db.db ".schema table_name"`
4. Check data integrity: run sample queries
5. Update models if schema changed

### Configuration Changes
1. Edit `src/config/settings.py` (ONLY place for config)
2. Validate with: `python -c "from src.config import settings; print(settings.to_dict())"`
3. Restart services that use config
4. Verify with health check

---

## Key System Behaviors

### Strategy Discovery Registry
- **Location**: `data/strategies/registry.json`
- **Purpose**: Track which strategies user has accepted/rejected
- **Behavior**: Discovery script MUST filter out known strategies
- **Test**: Run discovery twice - second run should show fewer/zero new discoveries

### Circuit Breakers
- **Purpose**: Prevent cascade failures when APIs fail
- **Behavior**: After 5 failures, circuit opens and uses cache
- **Reset**: Auto-reset after 60 seconds
- **Check**: `python -c "from src.utils.resilience import get_circuit_status; print(get_circuit_status())"`

### Health Monitoring
- **Checks**: Database, APIs, models, disk space, config
- **Output**: JSON status for each component
- **Usage**: `python -m src.health.health_check`
- **Server**: Can run as HTTP endpoint for external monitoring

### Automated Backups
- **Schedule**: Should be run daily (cron/Task Scheduler)
- **Location**: `backups/` directory with timestamps
- **Retention**: Keep 7 days by default
- **Restore**: `python scripts/backup_database.py --restore backups/TIMESTAMP`

---

## Data Sources and APIs

### Free Data (Always Available)
- **nflfastR**: Complete play-by-play data, updated weekly
- **ESPN API**: Live scores, game status (unofficial, rate-limited)

### Paid Data (Optional, Need Keys)
- **The Odds API**: Real-time odds from 20+ sportsbooks ($30/mo for 20K requests)
- **OddsJam**: Premium odds + injury data (contact for pricing)

### LLM APIs (Optional)
- **Grok 4.1**: Roast engine, ensemble voting ($5-15/M tokens)
- **GPT-4/Claude**: LLM Council predictions (varies by usage)

---

## Environment and Dependencies

### Required
Python 3.11+
pip install -r requirements.txt
# Core: pandas, numpy, scikit-learn, xgboost, streamlit, sqlite3

### Configuration Priority (Highest to Lowest)
1. Environment variables (`ODDS_API_KEY=...`)
2. `.env` file in project root
3. Streamlit secrets (`.streamlit/secrets.toml`)
4. `config.yaml` (legacy)
5. Defaults in `src/config/settings.py`

### Secrets Management
- **Local dev**: Use `.env` file (gitignored)
- **Production**: Use environment variables or secrets manager
- **Never commit**: API keys, database passwords, tokens

---

## Quality Standards

### Code Style
- Type hints required for new functions
- Docstrings for complex logic
- Maximum function length: 50 lines (prefer smaller)
- Maximum file length: 500 lines (prefer smaller)

### Testing
- Minimum 70% code coverage for new features
- Unit tests for pure functions
- Integration tests for database/API interactions
- End-to-end tests for critical paths

### Error Handling
- All external API calls must use circuit breakers
- All retries must use exponential backoff
- All database operations must handle connection failures
- All user inputs must be validated

---

## Success Criteria Checklist

Before claiming ANY task complete:

- [ ] Code written and files created
- [ ] Tests written and passing
- [ ] Manual verification performed (ran the code)
- [ ] Output/results shown in response
- [ ] Edge cases tested (what breaks it?)
- [ ] Health check still passes
- [ ] No regressions (old features still work)
- [ ] Documentation updated if needed
- [ ] Secrets/config handled properly
- [ ] Proof provided (not just claims)

---

## Emergency Procedures

### System Down
1. Run health check: `python -m src.health.health_check`
2. Check circuit breakers: `get_circuit_status()`
3. Review logs in console output
4. Restore from backup if needed

### Data Corruption
1. Stop all processes
2. List backups: `python scripts/backup_database.py --list`
3. Restore: `python scripts/backup_database.py --restore backups/TIMESTAMP`
4. Verify restore: run sample queries
5. Resume operations

### API Rate Limits
1. Check circuit breaker status (auto-handles this)
2. Increase cache TTL to reduce requests
3. Add delays between requests (already implemented)
4. Upgrade API tier if needed

---

## Remember

**"Show, don't tell."**

Every feature implementation should end with:
- Actual code execution
- Real output displayed
- Proof of correctness
- Edge case testing

If you can't prove it works, it's not done.