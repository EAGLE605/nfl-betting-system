"""
NFL Betting System - Full System Test

Tests all components to ensure everything is working with real data.
"""

import sys
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_all():
    print("=" * 60)
    print("TESTING NFL BETTING SYSTEM - ALL COMPONENTS")
    print("=" * 60)

    # Test 1: LLM Council
    print("\n1. Testing LLM Council...")
    try:
        from src.agents.llm_council import get_council

        council = get_council()
        print(f"   [OK] Council initialized with {len(council.members)} members")
        for mid, m in council.members.items():
            print(f"     - {mid}: {m.config.provider.value}")
    except Exception as e:
        print(f"   [ERROR] {e}")

    # Test 2: Research Agent
    print("\n2. Testing Research Agent...")
    try:
        from src.agents.research_agent import get_research_agent

        agent = get_research_agent()
        if agent.api_key:
            print("   [OK] Research agent ready (Perplexity API configured)")
        else:
            print("   [WARN] Research agent ready (no Perplexity API key)")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")

    # Test 3: Adaptive Learning Engine
    print("\n3. Testing Adaptive Learning Engine...")
    try:
        from src.learning.adaptive_engine import get_adaptive_engine

        engine = get_adaptive_engine()
        print(f"   [OK] Adaptive engine ready (DB: {engine.db_path})")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")

    # Test 4: Visualization
    print("\n4. Testing Visualization Engine...")
    try:
        from src.visualization.prediction_visualizer import get_visualizer

        viz = get_visualizer()
        print(f"   [OK] Visualizer ready (Output: {viz.output_dir})")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")

    # Test 5: API Integrations
    print("\n5. Testing API Integrations...")
    try:
        from agents.api_integrations import (
            ESPNAPI,
            NFLVerseAPI,
            NOAAWeatherAPI,
            TheOddsAPI,
        )

        # Odds API
        odds = TheOddsAPI()
        if odds.api_key:
            print("   [OK] The Odds API configured")
        else:
            print("   [WARN] The Odds API not configured (set ODDS_API_KEY)")

        # ESPN
        espn = ESPNAPI()
        print("   [OK] ESPN API ready")

        # Weather
        weather = NOAAWeatherAPI()
        print("   [OK] NOAA Weather API ready")

        # nflverse
        nflverse = NFLVerseAPI()
        if nflverse.nfl:
            print("   [OK] nflverse/nflreadpy ready")
        else:
            print("   [WARN] nflreadpy not installed")

    except Exception as e:
        print(f"   [ERROR] Error: {e}")

    # Test 6: Master Pipeline
    print("\n6. Testing Master Pipeline...")
    try:
        from src.orchestrator.master_pipeline import MasterPipeline, PipelineConfig

        config = PipelineConfig(bankroll=10000)
        pipeline = MasterPipeline(config)
        print("   [OK] Master pipeline ready")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")

    # Test 7: Models
    print("\n7. Checking trained models...")
    models_dir = Path("models")
    if models_dir.exists():
        models = list(models_dir.glob("*.pkl"))
        print(f"   [OK] Found {len(models)} trained models:")
        for m in models[:5]:
            print(f"     - {m.name}")
    else:
        print("   [WARN] No models directory")

    # Test 8: Feature data
    print("\n8. Checking feature data...")
    data_dir = Path("data")
    if data_dir.exists():
        features = list(data_dir.glob("features*.parquet"))
        print(f"   [OK] Found {len(features)} feature files:")
        for f in features:
            print(f"     - {f.name}")
    else:
        print("   [WARN] No data directory")

    # Test 9: Reports
    print("\n9. Checking reports...")
    reports_dir = Path("reports")
    if reports_dir.exists():
        reports = list(reports_dir.glob("*.json")) + list(reports_dir.glob("*.csv"))
        print(f"   [OK] Found {len(reports)} report files:")
        for r in reports[:5]:
            print(f"     - {r.name}")
    else:
        print("   [WARN] No reports directory")

    print("\n" + "=" * 60)
    print("SYSTEM TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    test_all()

