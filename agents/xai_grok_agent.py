"""
xAI Grok Integration for NFL Betting Analysis

Grok is xAI's advanced reasoning AI with real-time data access.
Perfect for analyzing game situations, sentiment, and making betting decisions.
"""

import json
import logging
from typing import Dict, List, Optional

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GrokAgent:
    """
    xAI Grok API Integration
    
    Features:
    - Real-time reasoning and analysis
    - Access to current events (via X/Twitter)
    - Advanced game situation analysis
    - Sentiment analysis
    - Betting edge identification
    """
    
    BASE_URL = "https://api.x.ai/v1"
    
    def __init__(self, api_key: str):
        """
        Initialize Grok API client.
        
        Args:
            api_key: Your xAI API key from x.ai
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        })
    
    def chat(self, 
             messages: List[Dict[str, str]], 
             model: str = "grok-2-1212",
             temperature: float = 0.0,
             stream: bool = False) -> Dict:
        """
        Send a chat completion request to Grok.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (grok-2-1212, grok-3, grok-4-fast-reasoning, etc.)
            temperature: 0.0 = deterministic, 1.0 = creative
            stream: Whether to stream the response
        
        Returns:
            Response from Grok API
        """
        url = f"{self.BASE_URL}/chat/completions"
        
        payload = {
            'messages': messages,
            'model': model,
            'temperature': temperature,
            'stream': stream
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        
        except Exception as e:
            logger.error(f"Grok API error: {e}")
            return {}
    
    def analyze_game(self, 
                    home_team: str, 
                    away_team: str, 
                    weather: Optional[Dict] = None,
                    injuries: Optional[List] = None,
                    odds: Optional[Dict] = None) -> str:
        """
        Get Grok's analysis of a game.
        
        Args:
            home_team: Home team name
            away_team: Away team name
            weather: Weather data (temp, wind, etc.)
            injuries: List of injuries
            odds: Current betting odds
        
        Returns:
            Grok's analysis and recommendations
        """
        # Build context
        context = f"Analyze this NFL game: {away_team} @ {home_team}\n\n"
        
        if weather:
            context += f"Weather: {weather.get('temperature')}°F, Wind: {weather.get('wind_speed')}\n"
        
        if injuries:
            context += f"Injuries: {', '.join(injuries)}\n"
        
        if odds:
            context += f"Current Line: {odds.get('spread')}, Total: {odds.get('total')}\n"
        
        context += "\nProvide: 1) Game analysis, 2) Key factors, 3) Betting edge opportunities"
        
        messages = [
            {
                'role': 'system',
                'content': 'You are an expert NFL analyst and betting advisor. Provide concise, data-driven insights.'
            },
            {
                'role': 'user',
                'content': context
            }
        ]
        
        response = self.chat(messages, temperature=0.0)
        
        if response and 'choices' in response:
            return response['choices'][0]['message']['content']
        
        return "Unable to get Grok analysis"
    
    def analyze_weather_edge(self, 
                            game: str,
                            weather: Dict,
                            total: float) -> str:
        """
        Get Grok's analysis of weather impact on totals.
        
        Args:
            game: Game description
            weather: Weather data
            total: Current total line
        
        Returns:
            Weather edge analysis
        """
        prompt = f"""
Analyze weather impact on NFL game total:

Game: {game}
Current Total: {total}
Temperature: {weather.get('temperature')}°F
Wind: {weather.get('wind_speed')}
Conditions: {weather.get('short_forecast')}

Historical data shows:
- Wind >15 MPH: Unders hit 62%
- Temp <25°F: Unders hit 56%
- Combined: Unders hit 65%+

Question: Does this weather create a betting edge on the total? If so, how many points adjustment and what's the recommended bet?
"""
        
        messages = [
            {'role': 'system', 'content': 'You are an expert NFL weather betting analyst.'},
            {'role': 'user', 'content': prompt}
        ]
        
        response = self.chat(messages, temperature=0.0)
        
        if response and 'choices' in response:
            return response['choices'][0]['message']['content']
        
        return "Unable to analyze weather edge"
    
    def sentiment_analysis(self, 
                          team: str,
                          reddit_posts: List[str]) -> str:
        """
        Analyze public sentiment (contrarian indicator).
        
        Args:
            team: Team name
            reddit_posts: List of post titles/content
        
        Returns:
            Sentiment analysis and betting implications
        """
        posts_text = "\n".join(reddit_posts[:20])  # Limit to 20 posts
        
        prompt = f"""
Analyze public betting sentiment for {team}:

Recent Reddit r/sportsbook posts:
{posts_text}

Question: Is the public heavily on {team}? Should we fade them (contrarian play)?
Provide: 1) Sentiment score, 2) Public betting %, 3) Recommendation
"""
        
        messages = [
            {'role': 'system', 'content': 'You are a betting sentiment analyst. Identify contrarian opportunities.'},
            {'role': 'user', 'content': prompt}
        ]
        
        response = self.chat(messages, temperature=0.0)
        
        if response and 'choices' in response:
            return response['choices'][0]['message']['content']
        
        return "Unable to analyze sentiment"
    
    def line_shopping_analysis(self, 
                               game: str,
                               odds_by_book: Dict) -> str:
        """
        Get Grok's recommendations on which book has best value.
        
        Args:
            game: Game description
            odds_by_book: Dict of {bookmaker: odds}
        
        Returns:
            Line shopping recommendations
        """
        odds_text = "\n".join([f"{book}: {odds}" for book, odds in odds_by_book.items()])
        
        prompt = f"""
Line shopping analysis for: {game}

Odds across sportsbooks:
{odds_text}

Question: Which book offers the best value? Calculate the edge vs average odds.
"""
        
        messages = [
            {'role': 'system', 'content': 'You are a professional line shopping expert.'},
            {'role': 'user', 'content': prompt}
        ]
        
        response = self.chat(messages, temperature=0.0)
        
        if response and 'choices' in response:
            return response['choices'][0]['message']['content']
        
        return "Unable to analyze line shopping"
    
    def predict_with_reasoning(self,
                              home_team: str,
                              away_team: str,
                              features: Dict) -> Dict:
        """
        Get Grok's prediction with detailed reasoning.
        
        Args:
            home_team: Home team
            away_team: Away team
            features: Model features (EPA, Elo, etc.)
        
        Returns:
            Dict with prediction, confidence, reasoning
        """
        features_text = "\n".join([f"{k}: {v}" for k, v in features.items()])
        
        prompt = f"""
NFL Game Prediction: {away_team} @ {home_team}

Key Metrics:
{features_text}

Provide:
1. Winner prediction (with confidence %)
2. Predicted score
3. Key reasoning factors
4. Betting recommendations (spread/total)
5. Risk assessment
"""
        
        messages = [
            {'role': 'system', 'content': 'You are an expert NFL analyst with access to advanced metrics.'},
            {'role': 'user', 'content': prompt}
        ]
        
        response = self.chat(messages, temperature=0.0)
        
        if response and 'choices' in response:
            content = response['choices'][0]['message']['content']
            return {
                'prediction': content,
                'raw_response': response
            }
        
        return {'prediction': 'Unable to generate prediction', 'raw_response': {}}


if __name__ == '__main__':
    # Test the Grok API
    import os
    
    API_KEY = 'your_xai_api_key_here'
    
    print("="*70)
    print("TESTING GROK (xAI) API")
    print("="*70)
    
    grok = GrokAgent(api_key=API_KEY)
    
    # Test 1: Simple chat
    print("\n1. Testing basic chat...")
    response = grok.chat([
        {'role': 'system', 'content': 'You are a test assistant.'},
        {'role': 'user', 'content': 'Testing. Just say hi and hello world and nothing else.'}
    ])
    
    if response and 'choices' in response:
        print(f"[OK] Response: {response['choices'][0]['message']['content']}")
    else:
        print("[ERROR] No response from Grok")
    
    # Test 2: Game analysis
    print("\n2. Testing game analysis...")
    analysis = grok.analyze_game(
        home_team='Kansas City Chiefs',
        away_team='Buffalo Bills',
        weather={'temperature': 35, 'wind_speed': '12 mph'},
        odds={'spread': -2.5, 'total': 47.5}
    )
    print(f"[ANALYSIS]\n{analysis}")
    
    # Test 3: Weather edge analysis
    print("\n3. Testing weather edge analysis...")
    weather_edge = grok.analyze_weather_edge(
        game='Green Bay Packers @ Chicago Bears',
        weather={'temperature': 22, 'wind_speed': '18 mph', 'short_forecast': 'Partly Cloudy'},
        total=42.5
    )
    print(f"[WEATHER EDGE]\n{weather_edge}")
    
    print("\n" + "="*70)
    print("GROK API TEST COMPLETE")
    print("="*70)

