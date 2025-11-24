#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-End Integration Tests

Tests complete workflows from data loading to bet generation.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
import json

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.backtest import prepare_predictions, filter_favorites_only
from src.betting.kelly import KellyCriterion


class E2ETester:
    """End-to-end integration testing."""
    
    def __init__(self):
        self.results = {"passed": [], "failed": []}
    
    def test_complete_workflow(self):
        """Test complete workflow: Data -> Model -> Prediction -> Filter -> Kelly -> Bet."""
        print("\n" + "="*80)
        print("E2E TEST: Complete Workflow")
        print("="*80)
        
        try:
            # Step 1: Load model
            print("\n[1] Loading model...")
            model_path = Path("models/xgboost_favorites_only.pkl")
            assert model_path.exists(), "Model not found"
            model = joblib.load(model_path)
            print(f"  [OK] Model loaded")
            
            # Step 2: Load features
            print("\n[2] Loading features...")
            features_path = Path("data/processed/features_2016_2024_improved.parquet")
            assert features_path.exists(), "Features not found"
            df = pd.read_parquet(features_path)
            
            # Load recommended features
            rec_path = Path("reports/recommended_features.csv")
            assert rec_path.exists(), "Recommended features not found"
            feature_cols = pd.read_csv(rec_path)['feature'].tolist()
            print(f"  [OK] Loaded {len(df):,} games, {len(feature_cols)} features")
            
            # Step 3: Prepare test data (2024 season)
            print("\n[3] Preparing test data...")
            test_df = df[df['season'] == 2024].copy()
            assert len(test_df) > 0, "No 2024 data"
            
            # Ensure all features exist
            missing = [f for f in feature_cols if f not in test_df.columns]
            for feat in missing:
                test_df[feat] = 0
            
            X_test = test_df[feature_cols].fillna(0)
            print(f"  [OK] Prepared {len(X_test)} test games")
            
            # Step 4: Generate predictions
            print("\n[4] Generating predictions...")
            proba = model.predict_proba(X_test)
            if proba.ndim == 1:
                test_df['pred_prob'] = proba
            else:
                test_df['pred_prob'] = proba[:, 1] if proba.shape[1] > 1 else proba[:, 0]
            
            # Add odds (simulated - in real system, get from API)
            test_df['odds'] = np.random.uniform(1.3, 2.5, len(test_df))
            print(f"  [OK] Generated {len(test_df)} predictions")
            print(f"      Avg probability: {test_df['pred_prob'].mean():.2%}")
            
            # Step 5: Filter favorites
            print("\n[5] Filtering favorites...")
            initial_count = len(test_df)
            filtered = filter_favorites_only(test_df)
            filtered_count = len(filtered)
            print(f"  [OK] Filtered {initial_count} -> {filtered_count} games ({filtered_count/initial_count*100:.1f}%)")
            
            # Step 6: Calculate Kelly sizing
            print("\n[6] Calculating bet sizes...")
            kelly = KellyCriterion(aggressive_mode=True)
            bankroll = 10000.0
            
            bets = []
            for _, row in filtered.iterrows():
                bet_size = kelly.calculate_bet_size(
                    row['pred_prob'],
                    row['odds'],
                    bankroll
                )
                if bet_size > 0:
                    bets.append({
                        'game_id': row.get('game_id', 'unknown'),
                        'prob': row['pred_prob'],
                        'odds': row['odds'],
                        'bet_size': bet_size
                    })
            
            print(f"  [OK] Generated {len(bets)} bet recommendations")
            if bets:
                avg_bet = np.mean([b['bet_size'] for b in bets])
                total_risk = sum([b['bet_size'] for b in bets])
                print(f"      Avg bet: ${avg_bet:.2f}")
                print(f"      Total risk: ${total_risk:.2f} ({total_risk/bankroll*100:.1f}% of bankroll)")
            
            # Step 7: Validate results
            print("\n[7] Validating results...")
            assert len(bets) > 0, "No bets generated"
            assert all(1.3 < b['odds'] < 2.0 for b in bets), "All bets should be favorites"
            assert all(b['bet_size'] > 0 for b in bets), "All bet sizes should be > 0"
            assert all(b['bet_size'] <= bankroll * 0.10 for b in bets), "No bet should exceed 10%"
            print(f"  [OK] All validations passed")
            
            print("\n" + "="*80)
            print("[SUCCESS] Complete workflow test PASSED")
            print("="*80)
            return True
            
        except Exception as e:
            print(f"\n[FAIL] Workflow test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_backtest_consistency(self):
        """Test that backtest results are consistent."""
        print("\n" + "="*80)
        print("E2E TEST: Backtest Consistency")
        print("="*80)
        
        try:
            # Load backtest metrics
            metrics_path = Path("reports/backtest_metrics.json")
            assert metrics_path.exists(), "Backtest metrics not found"
            
            with open(metrics_path) as f:
                metrics = json.load(f)
            
            # Validate metrics
            assert metrics['win_rate'] > 50, "Win rate should be > 50%"
            assert metrics['roi'] > 0, "ROI should be positive"
            assert metrics['total_bets'] > 0, "Should have bets"
            assert metrics['sharpe_ratio'] > 0, "Sharpe ratio should be positive"
            
            print(f"\n[OK] Backtest metrics validated:")
            print(f"     Win Rate: {metrics['win_rate']:.2f}%")
            print(f"     ROI: {metrics['roi']:.2f}%")
            print(f"     Total Bets: {metrics['total_bets']}")
            print(f"     Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
            
            # Load bet history and validate
            history_path = Path("reports/bet_history.csv")
            if history_path.exists():
                history = pd.read_csv(history_path)
                
                # Validate consistency
                calculated_wins = (history['result'] == 'win').sum() if 'result' in history.columns else history['result'].sum()
                calculated_rate = (calculated_wins / len(history)) * 100
                
                assert abs(calculated_rate - metrics['win_rate']) < 1.0, "Win rate mismatch"
                print(f"  [OK] Bet history consistent with metrics")
            
            print("\n[SUCCESS] Backtest consistency test PASSED")
            return True
            
        except Exception as e:
            print(f"\n[FAIL] Consistency test failed: {e}")
            return False
    
    def test_data_integrity(self):
        """Test data integrity and no leakage."""
        print("\n" + "="*80)
        print("E2E TEST: Data Integrity")
        print("="*80)
        
        try:
            # Load features
            features_path = Path("data/processed/features_2016_2024_improved.parquet")
            df = pd.read_parquet(features_path)
            
            # Load recommended features
            rec_path = Path("reports/recommended_features.csv")
            rec_features = pd.read_csv(rec_path)['feature'].tolist()
            
            # Check 1: No betting lines in recommended features
            leak_keywords = ['moneyline', 'spread', 'odds', 'line_movement', 'total_movement']
            leak_features = [f for f in rec_features if any(kw in f.lower() for kw in leak_keywords)]
            assert len(leak_features) == 0, f"Data leakage detected: {leak_features}"
            print(f"  [OK] No betting line features in recommendations")
            
            # Check 2: All recommended features exist in data
            missing = [f for f in rec_features if f not in df.columns]
            assert len(missing) == 0, f"Missing features: {missing}"
            print(f"  [OK] All recommended features exist in data")
            
            # Check 3: No NaN in critical columns
            critical_cols = ['game_id', 'gameday', 'season']
            for col in critical_cols:
                assert df[col].notna().all(), f"NaN values in {col}"
            print(f"  [OK] No NaN in critical columns")
            
            # Check 4: Temporal ordering
            df['gameday'] = pd.to_datetime(df['gameday'])
            assert df['gameday'].is_monotonic_increasing or df.groupby('season')['gameday'].is_monotonic_increasing.all(), "Data not temporally ordered"
            print(f"  [OK] Data is temporally ordered")
            
            print("\n[SUCCESS] Data integrity test PASSED")
            return True
            
        except Exception as e:
            print(f"\n[FAIL] Data integrity test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_all(self):
        """Run all E2E tests."""
        print("="*80)
        print("END-TO-END INTEGRATION TESTS")
        print("="*80)
        
        tests = [
            ("Complete Workflow", self.test_complete_workflow),
            ("Backtest Consistency", self.test_backtest_consistency),
            ("Data Integrity", self.test_data_integrity),
        ]
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    self.results["passed"].append(test_name)
                else:
                    self.results["failed"].append(test_name)
            except Exception as e:
                print(f"[FAIL] {test_name}: {e}")
                self.results["failed"].append(test_name)
        
        # Summary
        print("\n" + "="*80)
        print("E2E TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {len(tests)}")
        print(f"[OK] Passed: {len(self.results['passed'])}")
        print(f"[FAIL] Failed: {len(self.results['failed'])}")
        
        if self.results["passed"]:
            print("\n[OK] Passed:")
            for test in self.results["passed"]:
                print(f"   - {test}")
        
        if self.results["failed"]:
            print("\n[FAIL] Failed:")
            for test in self.results["failed"]:
                print(f"   - {test}")
        
        return len(self.results["failed"]) == 0


if __name__ == "__main__":
    tester = E2ETester()
    success = tester.run_all()
    sys.exit(0 if success else 1)

