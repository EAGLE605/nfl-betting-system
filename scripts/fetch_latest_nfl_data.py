#!/usr/bin/env python3
"""
Fetch Latest NFL Data from ESPN API
====================================
Downloads current week's games, scores, and odds from ESPN's public API.
No API key required!
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 70)
print("[ESPN] Fetching Latest NFL Data from ESPN API")
print("=" * 70)
print()

class ESPNDataFetcher:
    """Fetch NFL data from ESPN's public API."""
    
    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NFLBettingSystem/1.0',
            'Accept': 'application/json'
        })
    
    def get_current_week_games(self):
        """Get all games for the current week."""
        url = f"{self.BASE_URL}/scoreboard"
        
        try:
            print(f"[API] Fetching scoreboard from ESPN...")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract games
            games = []
            events = data.get('events', [])
            
            print(f"[OK] Found {len(events)} games")
            print()
            
            for event in events:
                game_info = self._parse_game(event)
                if game_info:
                    games.append(game_info)
                    
                    # Print game info
                    status = game_info['status']
                    away = game_info['away_team']
                    home = game_info['home_team']
                    away_score = game_info.get('away_score', '-')
                    home_score = game_info.get('home_score', '-')
                    
                    print(f"[GAME] {away} @ {home} | {away_score}-{home_score} | {status}")
            
            return games
            
        except Exception as e:
            print(f"[ERROR] Failed to fetch ESPN data: {e}")
            return []
    
    def _parse_game(self, event):
        """Parse a single game from ESPN data."""
        try:
            game_id = event.get('id')
            game_date = event.get('date')
            name = event.get('name', '')
            status_type = event.get('status', {}).get('type', {}).get('name', 'unknown')
            
            # Get competition data
            competitions = event.get('competitions', [])
            if not competitions:
                return None
            
            comp = competitions[0]
            
            # Get teams
            competitors = comp.get('competitors', [])
            if len(competitors) < 2:
                return None
            
            home_team = None
            away_team = None
            home_score = None
            away_score = None
            
            for competitor in competitors:
                team_info = competitor.get('team', {})
                team_abbr = team_info.get('abbreviation', '')
                team_score = competitor.get('score', '0')
                is_home = competitor.get('homeAway') == 'home'
                
                if is_home:
                    home_team = team_abbr
                    home_score = team_score
                else:
                    away_team = team_abbr
                    away_score = team_score
            
            # Get odds if available
            odds_data = comp.get('odds', [])
            spread = None
            over_under = None
            
            if odds_data:
                odds = odds_data[0]
                spread = odds.get('details', '')
                over_under = odds.get('overUnder')
            
            return {
                'game_id': game_id,
                'date': game_date,
                'name': name,
                'away_team': away_team,
                'home_team': home_team,
                'away_score': away_score,
                'home_score': home_score,
                'status': status_type,
                'spread': spread,
                'over_under': over_under
            }
            
        except Exception as e:
            print(f"[WARNING] Failed to parse game: {e}")
            return None
    
    def get_team_info(self):
        """Get all NFL teams."""
        url = f"{self.BASE_URL}/teams"
        
        try:
            print(f"[API] Fetching team data...")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            teams = []
            sports = data.get('sports', [])
            for sport in sports:
                leagues = sport.get('leagues', [])
                for league in leagues:
                    team_list = league.get('teams', [])
                    for team_entry in team_list:
                        team = team_entry.get('team', {})
                        teams.append({
                            'id': team.get('id'),
                            'abbreviation': team.get('abbreviation'),
                            'display_name': team.get('displayName'),
                            'location': team.get('location'),
                            'name': team.get('name')
                        })
            
            print(f"[OK] Found {len(teams)} teams")
            return teams
            
        except Exception as e:
            print(f"[ERROR] Failed to fetch team data: {e}")
            return []


def main():
    """Main execution."""
    fetcher = ESPNDataFetcher()
    
    # Fetch current week games
    games = fetcher.get_current_week_games()
    
    if games:
        # Save to JSON
        output_dir = Path("data/schedules")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / "current_week_games.json"
        
        with open(output_file, 'w') as f:
            json.dump({
                'fetched_at': datetime.now().isoformat(),
                'games': games
            }, f, indent=2)
        
        print()
        print("=" * 70)
        print(f"[COMPLETE] Saved {len(games)} games to {output_file}")
        print("=" * 70)
        
        # Summary stats
        completed = sum(1 for g in games if g['status'] in ['STATUS_FINAL', 'Final'])
        in_progress = sum(1 for g in games if g['status'] in ['STATUS_IN_PROGRESS', 'In Progress'])
        scheduled = sum(1 for g in games if g['status'] in ['STATUS_SCHEDULED', 'Scheduled'])
        
        print()
        print("[STATS] Game Status:")
        print(f"        - Completed: {completed}")
        print(f"        - In Progress: {in_progress}")
        print(f"        - Scheduled: {scheduled}")
        print()
        
        return True
    else:
        print("[ERROR] No games fetched")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

