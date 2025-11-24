"""
Test API Keys - Verify all configured API keys are working

Tests:
1. The Odds API (ODDS_API_KEY)
2. xAI Grok API (XAI_API_KEY)
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from agents.api_integrations import TheOddsAPI
from agents.xai_grok_agent import GrokAgent

# Load environment variables
env_path = project_root / 'config' / 'api_keys.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    print(f"[WARNING] {env_path} not found. Trying environment variables...")

def test_odds_api():
    """Test The Odds API"""
    print("\n" + "="*70)
    print("TESTING THE ODDS API")
    print("="*70)
    
    api_key = os.getenv('ODDS_API_KEY')
    if not api_key:
        print("[FAIL] ODDS_API_KEY not found in environment")
        return False
    
    print(f"[INFO] API Key: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        api = TheOddsAPI(api_key=api_key)
        
        # Test getting NFL odds
        print("\n[TEST] Fetching NFL odds...")
        odds = api.get_nfl_odds()
        
        if not odds:
            print("[FAIL] Failed to fetch odds - API may be down or key invalid")
            return False
        
        print(f"[OK] Successfully fetched odds for {len(odds)} games")
        
        # Show sample data
        if odds:
            game = odds[0]
            print(f"\n[INFO] Sample game: {game.get('away_team', 'N/A')} @ {game.get('home_team', 'N/A')}")
            print(f"[INFO] Bookmakers: {len(game.get('bookmakers', []))}")
            
            # Check API usage headers
            print(f"\n[OK] The Odds API is WORKING")
            print(f"[INFO] Check your dashboard for remaining requests")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Error testing Odds API: {e}")
        return False


def test_grok_api():
    """Test xAI Grok API"""
    print("\n" + "="*70)
    print("TESTING XAI GROK API")
    print("="*70)
    
    api_key = os.getenv('XAI_API_KEY')
    if not api_key:
        print("[FAIL] XAI_API_KEY not found in environment")
        return False
    
    print(f"[INFO] API Key: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        agent = GrokAgent(api_key=api_key)
        
        # Test simple chat
        print("\n[TEST] Sending test message to Grok...")
        messages = [
            {
                "role": "user",
                "content": "Say 'API test successful' if you can read this."
            }
        ]
        
        response = agent.chat(messages=messages, model="grok-2-1212")
        
        if not response:
            print("[FAIL] No response from Grok API")
            return False
        
        # Extract content
        if 'choices' in response and len(response['choices']) > 0:
            content = response['choices'][0].get('message', {}).get('content', '')
            print(f"[OK] Grok Response: {content[:100]}...")
            print(f"\n[OK] xAI Grok API is WORKING")
            return True
        else:
            print(f"[FAIL] Unexpected response format: {response}")
            return False
        
    except Exception as e:
        print(f"[FAIL] Error testing Grok API: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all API tests"""
    print("="*70)
    print("API KEYS TEST SUITE")
    print("="*70)
    print(f"\n[INFO] Loading API keys from: {env_path}")
    
    results = {}
    
    # Test Odds API
    results['odds_api'] = test_odds_api()
    
    # Test Grok API
    results['grok_api'] = test_grok_api()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for api_name, status in results.items():
        status_icon = "[OK]" if status else "[FAIL]"
        print(f"{status_icon} {api_name.upper()}: {'WORKING' if status else 'FAILED'}")
    
    all_working = all(results.values())
    
    if all_working:
        print("\n[OK] All API keys are working correctly!")
    else:
        print("\n[WARN] Some API keys failed. Check the errors above.")
        print("[INFO] Make sure:")
        print("  1. API keys are set in config/api_keys.env")
        print("  2. Keys are valid and not expired")
        print("  3. You have internet connectivity")
    
    print("="*70)
    
    return 0 if all_working else 1


if __name__ == '__main__':
    exit(main())

