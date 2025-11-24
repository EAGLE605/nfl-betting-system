#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stress Tests - Test system under extreme conditions.
"""

import sys
from pathlib import Path

import pandas as pd

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.backtest import filter_favorites_only
from src.betting.kelly import KellyCriterion


def test_stress_kelly():
    """Stress test Kelly criterion with extreme values."""
    print("\n" + "=" * 80)
    print("STRESS TEST: Kelly Criterion")
    print("=" * 80)

    kelly = KellyCriterion(aggressive_mode=True)
    bankroll = 10000.0

    test_cases = [
        ("Extreme favorite", 0.95, 1.05),
        ("Extreme underdog", 0.10, 5.00),
        ("Perfect edge", 0.80, 1.20),
        ("No edge", 0.50, 2.00),
        ("Negative edge", 0.40, 2.00),
        ("Very high bankroll", 0.70, 1.80, 1000000.0),
        ("Very low bankroll", 0.70, 1.80, 100.0),
    ]

    passed = 0
    failed = 0

    for test_name, prob, odds, *bankroll_override in test_cases:
        try:
            test_bankroll = bankroll_override[0] if bankroll_override else bankroll
            bet_size = kelly.calculate_bet_size(prob, odds, test_bankroll)

            # Validate
            assert bet_size >= 0, "Bet size should be >= 0"
            assert bet_size <= test_bankroll * 0.10, "Bet size should be <= 10%"

            print(f"  [OK] {test_name}: ${bet_size:.2f}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {test_name}: {e}")
            failed += 1

    print(f"\nResult: {passed} passed, {failed} failed")
    return failed == 0


def test_stress_filter():
    """Stress test favorites filter with edge cases."""
    print("\n" + "=" * 80)
    print("STRESS TEST: Favorites Filter")
    print("=" * 80)

    test_cases = [
        ("All favorites", [1.4, 1.5, 1.6, 1.7, 1.8, 1.9]),
        ("All underdogs", [2.1, 2.5, 3.0, 4.0]),
        ("Mixed", [1.2, 1.5, 1.9, 2.1, 2.5]),
        ("Boundary values", [1.3, 1.31, 1.99, 2.0]),
        ("Empty", []),
        ("Single favorite", [1.75]),
        ("Single underdog", [2.25]),
    ]

    passed = 0
    failed = 0

    for test_name, odds_list in test_cases:
        try:
            df = pd.DataFrame({"odds": odds_list})
            filtered = filter_favorites_only(df)

            # Validate
            if len(df) > 0:
                assert len(filtered) <= len(df), "Filtered should not exceed original"
                if len(filtered) > 0:
                    assert all(
                        (filtered["odds"] > 1.3) & (filtered["odds"] < 2.0)
                    ), "All should be favorites"

            print(f"  [OK] {test_name}: {len(df)} -> {len(filtered)}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {test_name}: {e}")
            failed += 1

    print(f"\nResult: {passed} passed, {failed} failed")
    return failed == 0


def test_stress_data():
    """Stress test data loading with large datasets."""
    print("\n" + "=" * 80)
    print("STRESS TEST: Data Loading")
    print("=" * 80)

    try:
        features_path = Path("data/processed/features_2016_2024_improved.parquet")
        if not features_path.exists():
            print("  [SKIP] Features file not found")
            return True

        # Load large dataset
        df = pd.read_parquet(features_path)
        print(f"  [OK] Loaded {len(df):,} games")

        # Test operations on large dataset
        print("  [TEST] Filtering by season...")
        filtered = df[df["season"] == 2024]
        print(f"  [OK] Filtered to {len(filtered):,} games")

        print("  [TEST] Calculating statistics...")
        stats = df.describe()
        print(f"  [OK] Calculated statistics: {len(stats)} columns")

        print("  [TEST] Memory usage...")
        memory_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
        print(f"  [OK] Memory usage: {memory_mb:.1f} MB")

        return True
    except Exception as e:
        print(f"  [FAIL] Data stress test: {e}")
        return False


def main():
    """Run all stress tests."""
    print("=" * 80)
    print("STRESS TEST SUITE")
    print("=" * 80)

    tests = [
        ("Kelly Criterion", test_stress_kelly),
        ("Favorites Filter", test_stress_filter),
        ("Data Loading", test_stress_data),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"[FAIL] {test_name}: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 80)
    print("STRESS TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    print(f"Total Tests: {total}")
    print(f"[OK] Passed: {passed}")
    print(f"[FAIL] Failed: {total - passed}")

    for test_name, success in results:
        status = "[OK]" if success else "[FAIL]"
        print(f"{status} {test_name}")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
