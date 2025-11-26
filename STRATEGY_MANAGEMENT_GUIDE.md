# 📋 Strategy Management System - Complete Guide

## 🎯 What Problem Does This Solve?

**THE PROBLEM YOU HAD:**
- Running strategy discovery multiple times showed the same recommendations
- No way to track which strategies you've accepted or rejected
- Duplicates kept appearing ("Prime-time unders" vs "Primetime unders")
- No version history when strategies improved

**THE SOLUTION:**
A complete strategy management system that:
- ✅ Remembers every strategy you've reviewed
- ✅ Detects duplicates with 85% similarity matching
- ✅ Tracks version updates when stats improve
- ✅ Provides a dashboard to manage everything
- ✅ Saves all data to `data/strategies/registry.json`

---

## 📚 Table of Contents

1. [Quick Start](#quick-start)
2. [How It Works (Beginner-Friendly)](#how-it-works)
3. [Dashboard Guide](#dashboard-guide)
4. [Using in Discovery Scripts](#using-in-discovery-scripts)
5. [API Reference](#api-reference)
6. [Examples](#examples)
7. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Step 1: Run the Test (See It Work!)

```bash
python test_strategy_registry.py
```

**What this does:**
- Creates 3 example strategies
- Tests duplicate detection
- Accepts/rejects strategies
- Creates a version update
- Saves everything to `data/strategies/registry.json`

### Step 2: View in Dashboard

```bash
python -m streamlit run dashboard/app.py
```

Then:
1. Click the **📋 STRATEGIES** tab
2. You'll see:
   - **⏳ Pending Review** - New strategies waiting for your decision
   - **✅ Active Strategies** - Strategies you're using
   - **❌ Rejected** - Strategies you tested and rejected
   - **📦 Archived** - Old strategies you stopped using

### Step 3: Review Strategies

For each pending strategy:
1. Click to expand the card
2. Review: Win Rate, ROI, Sample Size, Description
3. Add notes (optional): "Why I'm accepting/rejecting this"
4. Click **✅ Accept** or **❌ Reject**

---

## 🎓 How It Works (Beginner-Friendly)

### The Filing Cabinet Analogy

Think of the strategy registry like a filing cabinet:

```
📋 STRATEGY REGISTRY (Filing Cabinet)
│
├── 📁 PENDING (Inbox)
│   └── New strategies waiting for your review
│
├── 📁 ACCEPTED (Active Files)
│   └── Strategies you're currently using
│
├── 📁 REJECTED (Discarded)
│   └── Strategies you tested and didn't like
│
└── 📁 ARCHIVED (Old Files)
    └── Strategies that used to work but don't anymore
```

### How Duplicate Detection Works

**The Problem:**
```
"Prime-time unders after 3+ hour travel"
"Primetime unders 3hr+ travel"
```
These are 92% similar → Same strategy!

**The Solution:**
```python
# Fuzzy matching with SequenceMatcher
similarity = SequenceMatcher(None, pattern1, pattern2).ratio()

if similarity > 0.85:  # 85% or more = duplicate!
    print("⚠️ This strategy already exists!")
```

**What happens:**
- System compares new patterns to all existing ones
- If 85%+ similar → Shows warning
- You decide: "Is this actually the same strategy?"

### How Version Control Works

**Scenario:** Your strategy's stats improved!

```
Prime-time Unders v1:
  Win Rate: 60.3%
  ROI: 15.1%
  Sample: 67 games

Prime-time Unders v2 (IMPROVED!):
  Win Rate: 63.8%
  ROI: 20.1%
  Sample: 87 games
```

**What the system does:**
1. Creates new version (v2) with updated stats
2. Archives old version (v1) with note "Superseded by v2"
3. Sets v2 to PENDING (you need to re-review improved stats)

---

## 🖥️ Dashboard Guide

### Main Strategy Tab: 📋 STRATEGIES

#### Section 1: Summary Stats (Top of Page)

```
┌─────────────────────────────────────────────┐
│ Total: 10 | Pending: 3 | Accepted: 5       │
│ Rejected: 1 | Archived: 1                   │
└─────────────────────────────────────────────┘
```

Quick overview of your entire strategy collection.

#### Section 2: Sub-Tabs

##### ⏳ Pending Review

**What's here:** Newly discovered strategies waiting for your decision.

**What to do:**
1. Click strategy to expand
2. Read description and pattern
3. Check win rate, ROI, sample size
4. Add notes (why accepting/rejecting)
5. Click **✅ Accept** or **❌ Reject**

**Example Strategy Card:**

```
┌────────────────────────────────────────────────┐
│ Prime-time Unders (PENDING)                    │
├────────────────────────────────────────────────┤
│ Win Rate: 60.3%  │ ROI: 15.1%  │ Sample: 67   │
├────────────────────────────────────────────────┤
│ Description:                                    │
│ Bet unders in prime-time games when total > 45│
│                                                 │
│ Pattern:                                        │
│ game.primetime == True AND total_line > 45     │
│                                                 │
│ Conditions:                                     │
│ - primetime: True                              │
│ - total_line: >45                              │
│ - min_sample: 50                               │
├────────────────────────────────────────────────┤
│ [✅ Accept] [❌ Reject] [🗑️ Delete]            │
│ Add notes: ________________________            │
└────────────────────────────────────────────────┘
```

##### ✅ Active Strategies

**What's here:** Strategies you've accepted and are currently using.

**Features:**
- Shows all active strategies
- Performance summary (total bets, avg win rate, avg ROI)
- Can archive or reject if they stop working

**Actions:**
- **❌ Reject** - Move to rejected (if underperforming)
- **📦 Archive** - Stop using but keep for reference
- **🗑️ Delete** - Remove permanently (careful!)

##### ❌ Rejected

**What's here:** Strategies you tested and decided not to use.

**Why keep them?**
- Remember what didn't work
- See your notes on why you rejected them
- Can re-accept if conditions change

##### 📦 Archived

**What's here:** Strategies that were good but stopped working.

**Common reasons:**
- Market adjusted (everyone found this edge)
- Sample size was too small
- Conditions changed

##### ➕ Add New

**What's here:** Form to manually add a strategy.

**Use cases:**
- Found a strategy outside the automated system
- Manual backtest results
- Strategy from a friend or forum

**Required fields:**
- Name (e.g., "Prime-time unders")
- Description (what is it?)
- Pattern (the actual rule)
- Win rate, ROI, sample size, edge

**Optional:**
- Sharpe ratio
- Conditions (JSON format)

##### 🔍 Tools

**Duplicate Checker:**
```
Enter pattern: "Primetime unders total > 45"
                ↓
Result: ⚠️ Similar strategy found: Prime-time Unders (92% similar)
```

**Version Updater:**
- Select an accepted strategy
- Enter new improved stats
- System creates v2 and archives v1

---

## 🔧 Using in Discovery Scripts

### Integration Pattern

```python
from src.strategy_registry import StrategyRegistry, Strategy

# Initialize registry
registry = StrategyRegistry()

# Your discovery code finds a new strategy
new_pattern = "game.primetime == True AND total_line > 45"

# Check if already exists
existing = registry.find_similar_strategy(new_pattern, threshold=0.85)

if existing:
    print(f"⚠️ Duplicate found: {existing.name}")
    print("Skipping...")
else:
    # Create new strategy
    strategy = Strategy(
        strategy_id="primetime_unders_v1",
        name="Prime-time Unders",
        description="Bet unders in prime-time games",
        pattern=new_pattern,
        win_rate=60.3,
        roi=15.1,
        sample_size=67,
        edge=8.5
    )

    # Add to registry
    success, message = registry.add_strategy(strategy)
    if success:
        print(f"✅ Added new strategy: {strategy.name}")
    else:
        print(f"❌ Error: {message}")
```

### Update Existing Discovery Script

If you have a script like `scripts/bulldog_edge_discovery.py`:

```python
# Add to top of file
from src.strategy_registry import StrategyRegistry, Strategy

# In your discovery function
def discover_edges(data):
    registry = StrategyRegistry()

    # Your edge discovery logic...
    discovered_edges = find_patterns(data)

    for edge in discovered_edges:
        # Check registry before showing
        if registry.find_similar_strategy(edge['pattern']):
            continue  # Skip, already reviewed

        # Show only NEW discoveries
        print(f"NEW EDGE: {edge['name']}")
        print(f"  Win Rate: {edge['win_rate']}%")
        print(f"  ROI: {edge['roi']}%")

        # Prompt user
        accept = input("Accept? (y/n): ")

        if accept.lower() == 'y':
            strategy = Strategy(
                strategy_id=generate_id(edge['name']),
                name=edge['name'],
                description=edge['description'],
                pattern=edge['pattern'],
                win_rate=edge['win_rate'],
                roi=edge['roi'],
                sample_size=edge['sample_size'],
                edge=edge['edge']
            )
            registry.add_strategy(strategy)
            registry.accept_strategy(strategy.strategy_id)
```

---

## 📖 API Reference

### StrategyRegistry Class

#### `__init__(registry_path="data/strategies/registry.json")`

Initialize the registry.

**Args:**
- `registry_path` (str): Path to registry JSON file

**Example:**
```python
registry = StrategyRegistry()
# or custom path
registry = StrategyRegistry("my_strategies.json")
```

---

#### `add_strategy(strategy, skip_duplicate_check=False)`

Add a new strategy to the registry.

**Args:**
- `strategy` (Strategy): Strategy object to add
- `skip_duplicate_check` (bool): Skip duplicate detection (default: False)

**Returns:**
- `(success: bool, message: str)`

**Example:**
```python
strategy = Strategy(...)
success, message = registry.add_strategy(strategy)
if success:
    print(f"Added: {message}")
```

---

#### `accept_strategy(strategy_id, notes="")`

Accept a strategy (mark as ACCEPTED).

**Args:**
- `strategy_id` (str): ID of strategy
- `notes` (str): Why you accepted it

**Returns:**
- `(success: bool, message: str)`

**Example:**
```python
success, msg = registry.accept_strategy(
    "primetime_unders_v1",
    notes="Strong ROI, good sample size"
)
```

---

#### `reject_strategy(strategy_id, notes="")`

Reject a strategy (mark as REJECTED).

**Args:**
- `strategy_id` (str): ID of strategy
- `notes` (str): Why you rejected it

**Returns:**
- `(success: bool, message: str)`

**Example:**
```python
success, msg = registry.reject_strategy(
    "cold_weather_unders_v1",
    notes="Sample size too small, needs more data"
)
```

---

#### `find_similar_strategy(pattern, threshold=0.85)`

Find if a similar strategy already exists.

**Args:**
- `pattern` (str): Pattern to search for
- `threshold` (float): Similarity threshold (0.85 = 85%)

**Returns:**
- `Strategy` if found, `None` otherwise

**Example:**
```python
similar = registry.find_similar_strategy("Primetime unders", threshold=0.80)
if similar:
    print(f"Found: {similar.name} ({similar.similarity_score('Primetime unders') * 100:.1f}% similar)")
```

---

#### `create_strategy_version(original_id, updated_metrics)`

Create a new version of an existing strategy.

**Args:**
- `original_id` (str): ID of original strategy
- `updated_metrics` (dict): New performance metrics

**Returns:**
- `(success: bool, message: str)`

**Example:**
```python
improved = {
    "win_rate": 65.0,  # Was 60.0
    "roi": 20.0,       # Was 15.0
    "sample_size": 100  # Was 67
}
success, msg = registry.create_strategy_version(
    "primetime_unders_v1",
    improved
)
```

---

#### `get_pending_strategies()`

Get all pending strategies (need review).

**Returns:**
- `List[Strategy]`

**Example:**
```python
pending = registry.get_pending_strategies()
for strategy in pending:
    print(f"Review: {strategy.name} ({strategy.roi}% ROI)")
```

---

#### `get_accepted_strategies()`

Get all accepted strategies (currently using).

**Returns:**
- `List[Strategy]`

---

#### `get_stats()`

Get summary statistics.

**Returns:**
- `Dict` with keys: total, pending, accepted, rejected, archived

**Example:**
```python
stats = registry.get_stats()
print(f"You have {stats['accepted']} active strategies")
```

---

## 💡 Examples

### Example 1: Integrate with Existing Discovery Script

```python
# scripts/my_discovery.py

from src.strategy_registry import StrategyRegistry, Strategy

def run_discovery():
    registry = StrategyRegistry()

    # Your discovery logic
    edges = discover_edges_from_data()

    print(f"\nFound {len(edges)} potential edges")

    new_count = 0
    for edge in edges:
        # Skip if already in registry
        if registry.find_similar_strategy(edge['pattern']):
            continue

        # Only show NEW edges
        print(f"\n🆕 NEW EDGE: {edge['name']}")
        print(f"   Win Rate: {edge['win_rate']}%")
        print(f"   ROI: {edge['roi']}%")
        print(f"   Sample: {edge['sample_size']} games")

        # Auto-add to registry as PENDING
        strategy = Strategy(
            strategy_id=edge['name'].lower().replace(' ', '_') + '_v1',
            name=edge['name'],
            description=edge['description'],
            pattern=edge['pattern'],
            win_rate=edge['win_rate'],
            roi=edge['roi'],
            sample_size=edge['sample_size'],
            edge=edge['edge']
        )

        success, message = registry.add_strategy(strategy)
        if success:
            new_count += 1

    print(f"\n✅ Added {new_count} new strategies to pending review")
    print("Run the dashboard to review them!")

if __name__ == "__main__":
    run_discovery()
```

### Example 2: Batch Accept Strategies with Good Stats

```python
from src.strategy_registry import StrategyRegistry

registry = StrategyRegistry()
pending = registry.get_pending_strategies()

# Auto-accept strategies with ROI > 15% and sample > 100
for strategy in pending:
    if strategy.roi > 15 and strategy.sample_size > 100:
        registry.accept_strategy(
            strategy.strategy_id,
            notes=f"Auto-accepted: ROI {strategy.roi}% > 15%, Sample {strategy.sample_size} > 100"
        )
        print(f"✅ Auto-accepted: {strategy.name}")
```

### Example 3: Export Accepted Strategies to CSV

```python
import pandas as pd
from src.strategy_registry import StrategyRegistry

registry = StrategyRegistry()
accepted = registry.get_accepted_strategies()

# Convert to DataFrame
df = pd.DataFrame([
    {
        "Name": s.name,
        "Win Rate": s.win_rate,
        "ROI": s.roi,
        "Sample Size": s.sample_size,
        "Edge": s.edge,
        "Pattern": s.pattern
    }
    for s in accepted
])

# Save to CSV
df.to_csv("active_strategies.csv", index=False)
print(f"Exported {len(accepted)} strategies to active_strategies.csv")
```

---

## 🐛 Troubleshooting

### Issue: "Registry file not found"

**Cause:** Running the system for the first time.

**Solution:** This is normal! The system creates `data/strategies/registry.json` automatically.

---

### Issue: "Duplicate not detected even though strategies are similar"

**Cause:** Threshold too high (default 0.85 = 85% similar).

**Solution:** Lower the threshold:

```python
similar = registry.find_similar_strategy(pattern, threshold=0.75)  # 75% similar
```

**Trade-off:**
- Higher threshold (0.90): Fewer false positives, might miss some duplicates
- Lower threshold (0.70): Catches more duplicates, might flag different strategies

---

### Issue: "Can't update strategy version"

**Cause:** Original strategy not found or is not ACCEPTED.

**Solution:** Check the strategy status:

```python
strategy = registry.strategies.get("strategy_id")
if strategy:
    print(f"Status: {strategy.status}")
    if strategy.status != "accepted":
        print("Only accepted strategies can be versioned")
```

---

### Issue: "Dashboard shows old data after updating registry"

**Cause:** Streamlit caches session state.

**Solution:** Click the refresh button in the dashboard or refresh your browser.

---

### Issue: "Lost all my strategies!"

**Cause:** Registry file deleted or moved.

**Solution:** Check `data/strategies/registry.json`. If deleted, run the test script again to recreate examples.

**Prevention:** Back up your registry:

```bash
cp data/strategies/registry.json data/strategies/registry_backup.json
```

---

## 🎯 Best Practices

### 1. Review Strategies Regularly

Set a schedule:
- **Weekly:** Review pending strategies
- **Monthly:** Check if accepted strategies still perform
- **Quarterly:** Archive underperforming strategies

### 2. Write Good Notes

**Bad note:**
```
"Looks good"
```

**Good note:**
```
"Accepting because:
- Sample size > 100 games (confidence high)
- ROI 15.1% is strong
- Primetime games have consistent data
- Plan to test for 2 more weeks before betting real money"
```

### 3. Test Before Accepting

**Workflow:**
1. Strategy appears in PENDING
2. Add note: "Paper trading for 2 weeks"
3. Track performance manually
4. If good → ACCEPT with note "Paper trading successful"
5. If bad → REJECT with note "Paper trading showed 48% win rate, below threshold"

### 4. Use Version Control Wisely

**When to create a new version:**
- Stats improved significantly (> 5% ROI increase)
- Sample size doubled
- You modified the pattern/conditions

**When NOT to create a new version:**
- Minor fluctuations (58% → 59% win rate)
- Just one more game added to sample

### 5. Archive, Don't Delete

**When market changes:**
- Strategy stops working → ARCHIVE (don't delete!)
- Why? You might want to reference it later
- Note: "Archived 2025-11: Market adjusted, edge disappeared"

---

## 🚀 Next Steps

Now that you have strategy management set up:

1. **Integrate with discovery scripts**
   - Update any edge discovery code to use the registry
   - Prevent showing duplicates

2. **Build a monitoring dashboard**
   - Track live performance of accepted strategies
   - Alert when strategy underperforms

3. **Add backtesting integration**
   - When you accept a strategy, auto-run backtest
   - Validate stats before accepting

4. **Create strategy reports**
   - Export accepted strategies to PDF
   - Share with others (anonymized)

5. **Implement auto-discovery**
   - Run edge discovery weekly
   - Auto-add to registry as PENDING
   - Email you when new edges found

---

## 📞 Need Help?

- **Check examples:** `test_strategy_registry.py`
- **Read code comments:** All functions are heavily commented
- **Try the dashboard:** Best way to learn is by using it!

---

**Built with ❤️ for serious bettors who want to stay organized!**
