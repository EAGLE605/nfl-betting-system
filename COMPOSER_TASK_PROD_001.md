# 🎯 COMPOSER TASK PROD-001: Pre-Game Prediction Engine

**Priority**: CRITICAL  
**Estimated Time**: 2-3 hours  
**Dependencies**: NONE (can start immediately)  
**Status**: NOT STARTED

---

## 📋 **OBJECTIVE**

Build a complete pre-game prediction engine that runs 1 hour before each NFL game, generates predictions using the trained model, applies discovered edges, calculates expected value, and determines bet recommendations.

---

## 📁 **FILE TO CREATE**

**Path**: `scripts/pregame_prediction_engine.py`

**Size**: ~400-500 lines

---

## 🔧 **DETAILED REQUIREMENTS**

### **1. IMPORTS AND SETUP**

```python
"""
Pre-Game Prediction Engine

Runs 1 hour before each NFL game to:
1. Load the trained XGBoost model
2. Fetch live odds from The Odds API
3. Generate features for the upcoming game
4. Make predictions
5. Apply discovered edge filters
6. Calculate expected value
7. Determine bet recommendations
8. Output structured results

Usage:
    python scripts/pregame_prediction_engine.py --game-id 401671637
    python scripts/pregame_prediction_engine.py --all-today
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import logging
import os
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import pytz
import requests

# Local imports
from src.betting.kelly import KellyCriterion
from src.features.pipeline import FeaturePipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

---

### **2. ODDS API CLIENT CLASS**

**Requirements**:
- Fetch live odds from The Odds API
- Handle multiple sportsbooks
- Find best available odds (line shopping)
- Cache results to avoid API overuse
- Handle rate limiting and errors gracefully

```python
class OddsAPIClient:
    """Client for The Odds API."""
    
    def __init__(self, api_key: str):
        """
        Initialize Odds API client.
        
        Args:
            api_key: The Odds API key from config/api_keys.env
        """
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    def get_nfl_odds(self, markets: List[str] = None) -> List[Dict]:
        """
        Fetch current NFL odds from all sportsbooks.
        
        Args:
            markets: List of markets to fetch. Options:
                - 'h2h' (moneyline)
                - 'spreads'
                - 'totals'
                Default: ['h2h', 'spreads', 'totals']
        
        Returns:
            List of game odds dictionaries
            
        Example return:
            [{
                'id': '...',
                'sport_key': 'americanfootball_nfl',
                'commence_time': '2025-11-24T20:15:00Z',
                'home_team': 'San Francisco 49ers',
                'away_team': 'Carolina Panthers',
                'bookmakers': [...]
            }, ...]
        """
        if markets is None:
            markets = ['h2h', 'spreads', 'totals']
        
        # Check cache first
        cache_key = f"nfl_odds_{','.join(markets)}"
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if datetime.now().timestamp() - cached_time < self.cache_ttl:
                logger.info("Using cached odds data")
                return cached_data
        
        # Fetch from API
        url = f"{self.base_url}/sports/americanfootball_nfl/odds"
        params = {
            'apiKey': self.api_key,
            'regions': 'us',
            'markets': ','.join(markets),
            'oddsFormat': 'american'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Cache the result
            self.cache[cache_key] = (datetime.now().timestamp(), data)
            
            logger.info(f"Fetched odds for {len(data)} games")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching odds: {e}")
            return []
    
    def find_best_odds(self, game_odds: Dict, bet_type: str, team: str) -> Tuple[Optional[float], Optional[str]]:
        """
        Find best available odds across all sportsbooks.
        
        Args:
            game_odds: Single game odds dictionary from API
            bet_type: 'h2h', 'spreads', or 'totals'
            team: 'home' or 'away'
        
        Returns:
            Tuple of (best_odds, sportsbook_name)
            Returns (None, None) if no odds found
            
        Example:
            best_odds, book = find_best_odds(game, 'h2h', 'home')
            # Returns: (-110, 'DraftKings')
        """
        best_odds = None
        best_book = None
        
        for bookmaker in game_odds.get('bookmakers', []):
            for market in bookmaker.get('markets', []):
                if market['key'] != bet_type:
                    continue
                
                for outcome in market['outcomes']:
                    # Match team
                    is_match = False
                    if team == 'home' and outcome['name'] == game_odds['home_team']:
                        is_match = True
                    elif team == 'away' and outcome['name'] == game_odds['away_team']:
                        is_match = True
                    
                    if not is_match:
                        continue
                    
                    # Get odds (American format)
                    odds = outcome['price']
                    
                    # For favorites (negative odds), best = least negative
                    # For underdogs (positive odds), best = most positive
                    if best_odds is None:
                        best_odds = odds
                        best_book = bookmaker['title']
                    else:
                        if odds > 0 and odds > best_odds:  # Underdog
                            best_odds = odds
                            best_book = bookmaker['title']
                        elif odds < 0 and odds > best_odds:  # Favorite
                            best_odds = odds
                            best_book = bookmaker['title']
        
        return best_odds, best_book
    
    def american_to_decimal(self, american_odds: float) -> float:
        """
        Convert American odds to decimal odds.
        
        Args:
            american_odds: American format odds (e.g., -110, +150)
        
        Returns:
            Decimal odds (e.g., 1.91, 2.50)
        """
        if american_odds > 0:
            return (american_odds / 100) + 1
        else:
            return (100 / abs(american_odds)) + 1
    
    def american_to_probability(self, american_odds: float) -> float:
        """
        Convert American odds to implied probability.
        
        Args:
            american_odds: American format odds
        
        Returns:
            Implied probability (0-1)
        """
        if american_odds > 0:
            return 100 / (american_odds + 100)
        else:
            return abs(american_odds) / (abs(american_odds) + 100)
```

---

### **3. EDGE FILTER CLASS**

**Requirements**:
- Load discovered edges from `reports/bulldog_edges_discovered.csv`
- Check if a game meets any edge criteria
- Return matching edges with confidence levels
- Support multiple edges simultaneously

```python
class EdgeFilter:
    """Filters games based on discovered edges."""
    
    def __init__(self, edges_file: str = "reports/bulldog_edges_discovered.csv"):
        """
        Initialize edge filter.
        
        Args:
            edges_file: Path to discovered edges CSV file
        """
        self.edges_file = edges_file
        self.edges = self._load_edges()
        
    def _load_edges(self) -> pd.DataFrame:
        """Load discovered edges from CSV."""
        if not os.path.exists(self.edges_file):
            logger.warning(f"Edges file not found: {self.edges_file}")
            return pd.DataFrame()
        
        try:
            edges = pd.read_csv(self.edges_file)
            logger.info(f"Loaded {len(edges)} discovered edges")
            return edges
        except Exception as e:
            logger.error(f"Error loading edges: {e}")
            return pd.DataFrame()
    
    def check_edge(self, game_features: Dict, edge_name: str) -> bool:
        """
        Check if game meets criteria for specific edge.
        
        Args:
            game_features: Dictionary of game features
            edge_name: Name of edge to check
        
        Returns:
            True if edge criteria met, False otherwise
        """
        # Edge 1: Home Favorites (Elo > 100)
        if edge_name == "Home Favorites (Elo > 100)":
            home_elo = game_features.get('home_elo', 0)
            away_elo = game_features.get('away_elo', 0)
            elo_diff = home_elo - away_elo
            return elo_diff > 100
        
        # Edge 2: Late Season Mismatches
        elif edge_name == "Late Season Mismatches":
            week = game_features.get('week', 0)
            home_wins = game_features.get('home_wins', 0)
            away_wins = game_features.get('away_wins', 0)
            return week >= 15 and (home_wins - away_wins) >= 4
        
        # Edge 3: Cold Weather Home
        elif edge_name == "Cold Weather Home":
            temp = game_features.get('temperature', 70)
            roof = game_features.get('roof', 'outdoor')
            home_elo = game_features.get('home_elo', 0)
            away_elo = game_features.get('away_elo', 0)
            return temp < 40 and roof == 'outdoor' and home_elo > away_elo
        
        # Edge 4: Early Season Favorites
        elif edge_name == "Early Season Home Favorites":
            week = game_features.get('week', 0)
            home_elo = game_features.get('home_elo', 0)
            away_elo = game_features.get('away_elo', 0)
            elo_diff = home_elo - away_elo
            return week <= 4 and elo_diff > 50
        
        # Edge 5: Divisional Domination
        elif edge_name == "Divisional Domination":
            same_division = game_features.get('same_division', False)
            home_elo = game_features.get('home_elo', 0)
            away_elo = game_features.get('away_elo', 0)
            elo_diff = home_elo - away_elo
            return same_division and elo_diff > 120
        
        # Edge 6: Rest Advantage
        elif edge_name == "Rest Advantage":
            home_rest = game_features.get('home_rest_days', 7)
            away_rest = game_features.get('away_rest_days', 7)
            rest_diff = home_rest - away_rest
            return rest_diff >= 3
        
        return False
    
    def find_matching_edges(self, game_features: Dict) -> List[Dict]:
        """
        Find all edges that match this game.
        
        Args:
            game_features: Dictionary of game features
        
        Returns:
            List of matching edge dictionaries with metadata
            
        Example return:
            [{
                'edge_name': 'Home Favorites (Elo > 100)',
                'win_rate': 0.761,
                'roi': 0.452,
                'sample_size': 439,
                'confidence': 'S'
            }, ...]
        """
        matching = []
        
        if self.edges.empty:
            return matching
        
        for _, edge in self.edges.iterrows():
            edge_name = edge['edge_name']
            
            if self.check_edge(game_features, edge_name):
                matching.append({
                    'edge_name': edge_name,
                    'win_rate': edge['win_rate'],
                    'roi': edge['roi'],
                    'sample_size': edge['sample_size'],
                    'confidence': edge.get('confidence_tier', 'C'),
                    'p_value': edge.get('p_value', 1.0)
                })
        
        return matching
```

---

### **4. PREGAME ENGINE CLASS**

**Requirements**:
- Load trained model from `models/xgboost_improved.pkl` or `models/calibrated_model.pkl`
- Generate features for upcoming game
- Make predictions
- Apply edge filters
- Calculate expected value vs market odds
- Determine bet sizing using Kelly Criterion
- Output structured recommendations

```python
class PreGameEngine:
    """Main pre-game prediction engine."""
    
    def __init__(self, model_path: str = "models/calibrated_model.pkl"):
        """
        Initialize pre-game engine.
        
        Args:
            model_path: Path to trained model file
        """
        self.model_path = model_path
        self.model = self._load_model()
        self.feature_pipeline = FeaturePipeline()
        self.edge_filter = EdgeFilter()
        self.kelly = KellyCriterion()
        
        # Load API keys
        self.odds_api_key = os.getenv('ODDS_API_KEY')
        if not self.odds_api_key:
            logger.warning("ODDS_API_KEY not set - using dummy odds")
        
        self.odds_client = OddsAPIClient(self.odds_api_key) if self.odds_api_key else None
    
    def _load_model(self):
        """Load trained model from disk."""
        if not os.path.exists(self.model_path):
            logger.error(f"Model not found: {self.model_path}")
            raise FileNotFoundError(f"Model not found: {self.model_path}")
        
        try:
            with open(self.model_path, 'rb') as f:
                model = pickle.load(f)
            logger.info(f"Loaded model from {self.model_path}")
            return model
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def generate_features(self, game_info: Dict) -> Dict:
        """
        Generate features for a single game.
        
        Args:
            game_info: Game information dictionary with:
                - home_team: str
                - away_team: str
                - game_date: str (YYYY-MM-DD)
                - week: int
                - season: int
        
        Returns:
            Dictionary of features ready for model prediction
        """
        # This would use the FeaturePipeline to generate features
        # For now, return placeholder
        # TODO: Integrate with actual feature generation
        
        logger.info(f"Generating features for {game_info['away_team']} @ {game_info['home_team']}")
        
        # Placeholder - replace with actual feature generation
        features = {
            'home_elo': 1520,
            'away_elo': 1480,
            'home_rest_days': 7,
            'away_rest_days': 7,
            'temperature': 65,
            'roof': 'outdoor',
            'week': game_info.get('week', 12),
            'same_division': False,
            'home_wins': 7,
            'away_wins': 4
        }
        
        return features
    
    def predict_game(self, features: Dict) -> Dict:
        """
        Make prediction for game.
        
        Args:
            features: Dictionary of features
        
        Returns:
            Prediction dictionary with:
                - home_win_prob: float (0-1)
                - away_win_prob: float (0-1)
                - confidence: str ('high', 'medium', 'low')
        """
        # Convert features to DataFrame for model
        # (Placeholder - actual implementation would use full feature set)
        
        # For now, return placeholder prediction
        home_win_prob = 0.65
        away_win_prob = 0.35
        
        confidence = 'high' if abs(home_win_prob - 0.5) > 0.15 else 'medium'
        
        return {
            'home_win_prob': home_win_prob,
            'away_win_prob': away_win_prob,
            'confidence': confidence
        }
    
    def analyze_game(self, game_info: Dict) -> Dict:
        """
        Complete analysis of a single game.
        
        Args:
            game_info: Game information dictionary
        
        Returns:
            Complete analysis dictionary with predictions, edges, odds, and recommendations
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"ANALYZING: {game_info['away_team']} @ {game_info['home_team']}")
        logger.info(f"{'='*80}")
        
        # Step 1: Generate features
        features = self.generate_features(game_info)
        
        # Step 2: Make prediction
        prediction = self.predict_game(features)
        
        # Step 3: Get live odds
        if self.odds_client:
            all_odds = self.odds_client.get_nfl_odds()
            game_odds = self._find_game_odds(all_odds, game_info)
        else:
            game_odds = None
        
        # Step 4: Check for matching edges
        matching_edges = self.edge_filter.find_matching_edges(features)
        
        # Step 5: Calculate expected value
        recommendations = self._generate_recommendations(
            prediction, game_odds, matching_edges, game_info
        )
        
        return {
            'game_info': game_info,
            'features': features,
            'prediction': prediction,
            'odds': game_odds,
            'matching_edges': matching_edges,
            'recommendations': recommendations
        }
    
    def _find_game_odds(self, all_odds: List[Dict], game_info: Dict) -> Optional[Dict]:
        """Find odds for specific game."""
        # Match by team names
        for game in all_odds:
            if (game['home_team'] in game_info['home_team'] or 
                game_info['home_team'] in game['home_team']):
                return game
        return None
    
    def _generate_recommendations(self, prediction: Dict, odds: Optional[Dict], 
                                   edges: List[Dict], game_info: Dict) -> List[Dict]:
        """
        Generate bet recommendations.
        
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        # Only recommend if we have matching edges
        if not edges:
            logger.info("No matching edges - SKIP")
            return recommendations
        
        # Get best edge
        best_edge = max(edges, key=lambda x: x['roi'])
        
        logger.info(f"\nMATCHING EDGE: {best_edge['edge_name']}")
        logger.info(f"  Win Rate: {best_edge['win_rate']:.1%}")
        logger.info(f"  Historical ROI: {best_edge['roi']:.1%}")
        
        # Determine bet recommendation
        home_prob = prediction['home_win_prob']
        
        # If home team is the play (based on edge)
        if home_prob > 0.52:  # Minimum threshold
            # Get best odds
            if odds and self.odds_client:
                best_odds, book = self.odds_client.find_best_odds(odds, 'h2h', 'home')
                
                if best_odds:
                    # Calculate expected value
                    implied_prob = self.odds_client.american_to_probability(best_odds)
                    ev = (home_prob * (1 / implied_prob - 1)) - (1 - home_prob)
                    
                    # Only recommend if positive EV
                    if ev > 0:
                        # Calculate Kelly bet size
                        kelly_fraction = self.kelly.calculate_kelly(
                            win_prob=home_prob,
                            odds_decimal=self.odds_client.american_to_decimal(best_odds),
                            fraction=0.25  # Quarter Kelly
                        )
                        
                        recommendations.append({
                            'bet_type': 'moneyline',
                            'team': game_info['home_team'],
                            'side': 'home',
                            'odds': best_odds,
                            'sportsbook': book,
                            'win_probability': home_prob,
                            'expected_value': ev,
                            'kelly_fraction': kelly_fraction,
                            'edge_name': best_edge['edge_name'],
                            'confidence_tier': best_edge['confidence']
                        })
        
        return recommendations
```

---

### **5. MAIN EXECUTION**

```python
def main():
    """Main execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Pre-Game Prediction Engine')
    parser.add_argument('--game-id', help='Specific ESPN game ID')
    parser.add_argument('--all-today', action='store_true', help='Analyze all games today')
    parser.add_argument('--output', default='reports/pregame_analysis.json', 
                       help='Output file path')
    
    args = parser.parse_args()
    
    # Initialize engine
    engine = PreGameEngine()
    
    # Get games to analyze
    if args.game_id:
        # Single game
        games = [{
            'game_id': args.game_id,
            'home_team': 'San Francisco 49ers',
            'away_team': 'Carolina Panthers',
            'week': 12,
            'season': 2025
        }]
    elif args.all_today:
        # Get today's games from schedule
        from scripts.production_daily_pipeline import NFLScheduleManager
        schedule_mgr = NFLScheduleManager()
        games = schedule_mgr.get_today_schedule()
    else:
        logger.error("Must specify --game-id or --all-today")
        return
    
    # Analyze each game
    results = []
    for game in games:
        try:
            analysis = engine.analyze_game(game)
            results.append(analysis)
            
            # Print recommendations
            if analysis['recommendations']:
                print(f"\n{'='*80}")
                print(f"RECOMMENDATIONS FOR {game['away_team']} @ {game['home_team']}")
                print(f"{'='*80}")
                for rec in analysis['recommendations']:
                    print(f"\nBET: {rec['team']} {rec['bet_type'].upper()}")
                    print(f"  Odds: {rec['odds']} ({rec['sportsbook']})")
                    print(f"  Win Probability: {rec['win_probability']:.1%}")
                    print(f"  Expected Value: {rec['expected_value']:.2%}")
                    print(f"  Kelly Fraction: {rec['kelly_fraction']:.3f}")
                    print(f"  Edge: {rec['edge_name']}")
                    print(f"  Confidence: Tier {rec['confidence_tier']}")
            else:
                print(f"\nNO RECOMMENDATIONS for {game['away_team']} @ {game['home_team']}")
        
        except Exception as e:
            logger.error(f"Error analyzing game: {e}", exc_info=True)
    
    # Save results
    output_dir = Path(args.output).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"\nResults saved to: {args.output}")
    logger.info(f"Analyzed {len(results)} games")
    logger.info(f"Recommendations: {sum(len(r['recommendations']) for r in results)}")


if __name__ == "__main__":
    main()
```

---

## ✅ **ACCEPTANCE CRITERIA**

### **MUST HAVE**:
1. ✅ Script runs without errors
2. ✅ Loads trained model successfully
3. ✅ Fetches live odds from The Odds API
4. ✅ Generates features for games
5. ✅ Makes predictions
6. ✅ Applies edge filters correctly
7. ✅ Calculates expected value
8. ✅ Outputs structured JSON results
9. ✅ Handles errors gracefully
10. ✅ Logs all important steps

### **TESTING REQUIREMENTS**:
1. Test with `--game-id` argument
2. Test with `--all-today` argument
3. Test with missing API key (graceful degradation)
4. Test with no matching edges (skip game)
5. Test with matching edge (generate recommendation)
6. Verify odds fetching works
7. Verify Kelly calculation is correct
8. Verify JSON output is valid

---

## 📝 **NOTES FOR COMPOSER**

### **Integration Points**:
- Uses `src/betting/kelly.py` (already exists)
- Uses `src/features/pipeline.py` (already exists)
- Reads from `reports/bulldog_edges_discovered.csv` (already exists)
- Loads model from `models/calibrated_model.pkl` (already exists)

### **External APIs**:
- The Odds API: https://api.the-odds-api.com/v4/
- Documentation: https://the-odds-api.com/liveapi/guides/v4/
- Rate limit: 500 requests/month (free tier)

### **Error Handling**:
- API failures should be logged but not crash the script
- Missing model should raise clear error
- Missing edges file should warn but continue
- Invalid features should be logged and skipped

### **Output Format**:
```json
{
  "game_info": {...},
  "features": {...},
  "prediction": {
    "home_win_prob": 0.65,
    "away_win_prob": 0.35,
    "confidence": "high"
  },
  "odds": {...},
  "matching_edges": [...],
  "recommendations": [
    {
      "bet_type": "moneyline",
      "team": "San Francisco 49ers",
      "odds": -180,
      "sportsbook": "DraftKings",
      "win_probability": 0.65,
      "expected_value": 0.08,
      "kelly_fraction": 0.032,
      "edge_name": "Home Favorites (Elo > 100)",
      "confidence_tier": "S"
    }
  ]
}
```

---

## 🚀 **EXECUTION COMMAND**

```bash
# Test with specific game
python scripts/pregame_prediction_engine.py --game-id 401671637

# Analyze all games today
python scripts/pregame_prediction_engine.py --all-today

# Custom output location
python scripts/pregame_prediction_engine.py --all-today --output reports/today_bets.json
```

---

**STATUS**: Ready for Composer 1 to implement  
**PRIORITY**: CRITICAL  
**BLOCKING**: PROD-002 (depends on this output)

