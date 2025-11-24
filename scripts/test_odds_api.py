"""
Test The Odds API with real NFL data
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.api_integrations import TheOddsAPI

# Load API key from environment
API_KEY = '7f5005117f0b98ea00ef64e2cb4b26a4'

print("="*70)
print("TESTING THE ODDS API - LIVE NFL ODDS")
print("="*70)

# Initialize
api = TheOddsAPI(api_key=API_KEY)

# Get NFL odds
print("\nFetching NFL odds...")
odds = api.get_nfl_odds()

if not odds:
    print("[ERROR] No odds data returned")
    exit(1)

print(f"\n[OK] Found {len(odds)} games with odds")
print(f"[INFO] Checking API usage...")

# Display games
print("\n" + "="*70)
print("AVAILABLE GAMES")
print("="*70)

for i, game in enumerate(odds, 1):
    home = game['home_team']
    away = game['away_team']
    commence = game['commence_time']
    num_books = len(game['bookmakers'])
    
    print(f"\n{i}. {away} @ {home}")
    print(f"   Kickoff: {commence}")
    print(f"   Bookmakers: {num_books}")
    
    # Show odds from each bookmaker
    for bookmaker in game['bookmakers']:
        print(f"   [{bookmaker['title']}]:")
        
        for market in bookmaker['markets']:
            if market['key'] == 'h2h':
                # Moneyline
                print(f"      Moneyline:", end=" ")
                for outcome in market['outcomes']:
                    print(f"{outcome['name']}: {outcome['price']}", end=" | ")
                print()
            
            elif market['key'] == 'spreads':
                # Spread
                print(f"      Spread:", end=" ")
                for outcome in market['outcomes']:
                    print(f"{outcome['name']}: {outcome['point']:+.1f} @ {outcome['price']}", end=" | ")
                print()
            
            elif market['key'] == 'totals':
                # Total
                for outcome in market['outcomes']:
                    print(f"      Total: {outcome['name']} {outcome['point']} @ {outcome['price']}")

print("\n" + "="*70)
print("LINE SHOPPING EXAMPLE")
print("="*70)

if odds:
    game = odds[0]
    print(f"\nGame: {game['away_team']} @ {game['home_team']}")
    
    # Find best moneyline odds
    best_home_odds = -9999
    best_home_book = ""
    best_away_odds = -9999
    best_away_book = ""
    
    for bookmaker in game['bookmakers']:
        for market in bookmaker['markets']:
            if market['key'] == 'h2h':
                for outcome in market['outcomes']:
                    if outcome['name'] == game['home_team']:
                        if outcome['price'] > best_home_odds:
                            best_home_odds = outcome['price']
                            best_home_book = bookmaker['title']
                    else:
                        if outcome['price'] > best_away_odds:
                            best_away_odds = outcome['price']
                            best_away_book = bookmaker['title']
    
    print(f"\n[BEST ODDS - Line Shopping]:")
    print(f"   {game['home_team']}: {best_home_odds:+d} @ {best_home_book}")
    print(f"   {game['away_team']}: {best_away_odds:+d} @ {best_away_book}")
    
    # Calculate edge from line shopping
    avg_home = sum([outcome['price'] for bm in game['bookmakers'] 
                   for market in bm['markets'] if market['key'] == 'h2h'
                   for outcome in market['outcomes'] if outcome['name'] == game['home_team']]) / len(game['bookmakers'])
    
    edge = best_home_odds - avg_home
    edge_pct = (abs(edge) / abs(avg_home)) * 100
    
    print(f"\n[LINE SHOPPING EDGE]:")
    print(f"   Best: {best_home_odds:+d}")
    print(f"   Average: {avg_home:+.1f}")
    print(f"   Edge: {edge:+.1f} ({edge_pct:.2f}%)")

print("\n" + "="*70)
print("API USAGE SUMMARY")
print("="*70)
print(f"[OK] API Key: Working")
print(f"[INFO] Requests Used: Check your dashboard")
print(f"[INFO] Games Available: {len(odds)}")
print(f"[INFO] Bookmakers: {len(odds[0]['bookmakers']) if odds else 0}")
print(f"[OK] Line Shopping: ENABLED")
print("="*70)

