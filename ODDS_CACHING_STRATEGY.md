# ODDS DATA CACHING STRATEGY

## The Problem

- **Free tier:** 500 API calls/month (~16/day)
- **Odds update frequency:** Frequently but not every second
- **Current system:** Fetches fresh data every time (wasteful)
- **User experience:** Slow responses, risk of hitting limit

## The Solution: Multi-Layer Cache

### LAYER 1: Hot Cache (In-Memory)

**What:** Redis or simple Python dict in memory  
**TTL:** 5 minutes  
**Use Case:** Repeated requests within same session

```
Request → Check memory (5min TTL) → If fresh, return
                                  → If stale, go to Layer 2
```

**Why 5 minutes?**
- Odds don't change meaningfully in 5 min
- Dashboard refreshes feel instant
- Multiple picks requests = 1 API call

### LAYER 2: Warm Cache (Local Files)

**What:** JSON files in `data/odds_cache/`  
**TTL:** 30 minutes  
**Structure:**

```
data/odds_cache/
  ├── 2025-11-24_14-30_odds.json    # Timestamped snapshots
  ├── 2025-11-24_15-00_odds.json
  └── latest.json                    # Symlink to most recent
```

**Logic:**
```
If no memory cache:
  → Check local file timestamp
  → If < 30min old, load from file
  → If > 30min old, fetch fresh from API
  → Save new snapshot
```

**Benefits:**
- System restart doesn't lose data
- Can run offline with stale data (better than nothing)
- Historical snapshots for analysis

### LAYER 3: Cold Storage (Historical Database)

**What:** SQLite database `data/odds_history.db`  
**TTL:** Forever (keep all historical odds)  
**Schema:**

```sql
CREATE TABLE odds_snapshots (
    id INTEGER PRIMARY KEY,
    fetch_timestamp DATETIME,
    game_id TEXT,
    home_team TEXT,
    away_team TEXT,
    commence_time DATETIME,
    bookmaker TEXT,
    spread_line REAL,
    spread_odds REAL,
    home_ml REAL,
    away_ml REAL,
    total_line REAL,
    over_odds REAL,
    under_odds REAL
);

CREATE INDEX idx_game_time ON odds_snapshots(game_id, fetch_timestamp);
```

**Use Cases:**
- Line movement tracking (see how odds changed over time)
- Closing Line Value (CLV) calculation
- Model training on historical odds
- Sharp money detection

## SMART FETCH LOGIC

### Decision Tree

```
User requests picks
  ↓
Check memory cache (< 5min?)
  ├─ YES → Return instantly
  ↓
  NO → Check file cache (< 30min?)
      ├─ YES → Load from file, populate memory
      ↓
      NO → Check game time
          ├─ Game starts in < 2 hours?
          │   → Fetch fresh (odds move fast near kickoff)
          ├─ Game starts in 2-24 hours?
          │   → Use 30min cached (acceptable staleness)
          └─ Game starts > 24 hours?
              → Use 1hr cached (odds rarely move)
```

### Dynamic TTL Based on Context

| Time Until Kickoff | Cache TTL | Why |
|-------------------|-----------|-----|
| < 1 hour | 2 minutes | Odds moving fast |
| 1-6 hours | 15 minutes | Moderate movement |
| 6-24 hours | 30 minutes | Stable odds |
| > 24 hours | 1 hour | Very stable |

## API RATE LIMIT PROTECTION

### Request Counter

```python
# Track API usage
api_usage = {
    'daily_count': 0,
    'monthly_count': 21,  # From API response header
    'last_reset': '2025-11-24',
    'limit': 500
}
```

### Safety Checks

**Before API call:**
```
→ Check remaining calls
→ If < 50 remaining this month:
    → Show warning
    → Increase cache TTL to 1 hour
→ If < 10 remaining:
    → STOP fetching
    → Use cached data only
    → Alert user: "Rate limit approaching"
```

## CACHE INVALIDATION STRATEGIES

### When to Force Refresh

- User clicks "Refresh" button → Bypass all caches
- Injury news breaks → Invalidate affected game
- Line movement alert → Fetch specific game
- Manual override → `--force-refresh` flag

### Automatic Invalidation

```python
# Invalidate if:
- TTL expired (time-based)
- Game started (status changed)
- Odds moved > 3 points (significant change detected)
- New bookmaker added (more data available)
```

## IMPLEMENTATION APPROACH

### Option A: Simple (Start Here)

**File-based caching only:**
- `data/odds_cache/YYYY-MM-DD_HH-MM.json`
- 30-minute TTL
- ~50 lines of code
- Works immediately

**Pros:**
- Simple, no dependencies
- Transparent (can inspect files)
- Works offline

**Cons:**
- Slower than memory cache
- Manual cleanup needed

### Option B: Production-Ready

**Redis + File backup:**
- Redis for hot cache (instant access)
- Files for persistence
- SQLite for history

**Pros:**
- Blazing fast
- Automatic expiration
- Scalable to web dashboard

**Cons:**
- Requires Redis installation
- More complex

### Option C: Hybrid (Recommended)

**In-memory dict + file cache:**

```python
class OddsCache:
    def __init__(self):
        self._memory = {}  # In-memory cache
        self._cache_dir = Path("data/odds_cache")
        
    def get(self, key):
        # Try memory first
        if key in self._memory and not self._is_stale(key):
            return self._memory[key]
            
        # Try file cache
        cached_file = self._find_recent_cache(key)
        if cached_file:
            data = json.load(cached_file.open())
            self._memory[key] = data  # Populate memory
            return data
            
        # Cache miss - fetch from API
        return None
```

**Pros:**
- Fast (memory) + persistent (files)
- No external dependencies
- Simple to implement (~100 lines)

**Cons:**
- Memory not shared across processes

## FILE STRUCTURE

```
data/
  ├── odds_cache/
  │   ├── 2025-11-24_09-00_all_games.json
  │   ├── 2025-11-24_09-30_all_games.json
  │   ├── 2025-11-24_10-00_all_games.json
  │   └── latest.json → symlink
  ├── odds_history.db              # SQLite (optional)
  └── cache_stats.json             # Track cache hits/misses
```

### Cache Stats Example

```json
{
  "total_requests": 47,
  "cache_hits": 39,
  "cache_misses": 8,
  "api_calls_saved": 39,
  "hit_rate": "83%",
  "estimated_cost_saved": "$0.00"
}
```

## USER EXPERIENCE

### Dashboard Shows

```
Last updated: 5 minutes ago [Refresh Now]
Cache: 15 games loaded (fresh)
API calls remaining: 479/500
```

### CLI Output

```
$ python scripts/generate_daily_picks.py
[CACHE] Loading odds... (cached 3m ago)
[OK] 17 games loaded
[INFO] API calls saved: 1 (479 remaining this month)
```

## RECOMMENDED IMPLEMENTATION ORDER

### Phase 1: Basic File Cache (Today - 1 hour)
- Save API responses to `data/odds_cache/`
- Check timestamp before fetching
- 30-minute TTL

### Phase 2: Smart TTL (Tomorrow - 30 min)
- Dynamic TTL based on game time
- Rate limit protection
- Cache stats tracking

### Phase 3: Memory Layer (Later - 1 hour)
- Add in-memory dict cache
- 5-minute TTL for hot data
- Dashboard feels instant

### Phase 4: Historical DB (Optional - 2 hours)
- SQLite for line movement tracking
- CLV calculation
- Sharp money detection

## THE APPLE APPROACH

**What the user sees:**
- Picks load instantly
- Never hits rate limit
- System "just works"

**What they never see:**
- Cache logic
- File management
- TTL calculations
- API call optimization

**The technology disappears. The experience feels inevitable.**

---

## NEXT STEPS

Ready to implement **Phase 1 (basic file cache)**? It's the biggest bang for buck - saves API calls immediately with minimal code.

