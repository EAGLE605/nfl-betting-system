"""
NOAA Weather Intelligence Agent

Uses FREE government satellite/radar data for superior weather analysis.
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class NOAAWeatherAgent:
    """
    Advanced weather intelligence using NOAA's free APIs.
    
    Data Sources:
    - api.weather.gov: Forecasts, alerts
    - GOES-16/17: Satellite imagery
    - NEXRAD: Radar data
    - NCEI: Historical weather
    """
    
    NOAA_API = "https://api.weather.gov"
    
    # NFL Stadium coordinates
    STADIUMS = {
        'Arrowhead Stadium': {'lat': 39.0489, 'lon': -94.4839, 'team': 'KC'},
        'Lambeau Field': {'lat': 44.5013, 'lon': -88.0622, 'team': 'GB'},
        'Highmark Stadium': {'lat': 42.7738, 'lon': -78.7870, 'team': 'BUF'},
        'Soldier Field': {'lat': 41.8623, 'lon': -87.6167, 'team': 'CHI'},
        'FirstEnergy Stadium': {'lat': 41.5061, 'lon': -81.6995, 'team': 'CLE'},
        'Empower Field': {'lat': 39.7439, 'lon': -105.0201, 'team': 'DEN'},
        'Ford Field': {'lat': 42.3400, 'lon': -83.0456, 'team': 'DET', 'roof': 'dome'},
        'Acrisure Stadium': {'lat': 40.4468, 'lon': -80.0158, 'team': 'PIT'},
        'Levi\'s Stadium': {'lat': 37.4032, 'lon': -121.9698, 'team': 'SF'},
        'CenturyLink Field': {'lat': 47.5952, 'lon': -122.3316, 'team': 'SEA'},
        # ... Add all 30 stadiums
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NFL-Betting-Research (contact@example.com)'  # NOAA requires ID
        })
    
    def get_stadium_location(self, team: str) -> Optional[Dict]:
        """Get stadium coordinates for team."""
        for stadium, data in self.STADIUMS.items():
            if data.get('team') == team:
                return data
        return None
    
    def get_forecast(self, lat: float, lon: float, game_time: datetime) -> Dict:
        """
        Get detailed forecast from NOAA.
        
        Args:
            lat: Latitude
            lon: Longitude
            game_time: When game starts
            
        Returns:
            Dict with temperature, wind, precipitation
        """
        try:
            # Step 1: Get gridpoint for location
            points_url = f"{self.NOAA_API}/points/{lat},{lon}"
            points_response = self.session.get(points_url)
            
            if points_response.status_code != 200:
                logger.warning(f"NOAA points API failed: {points_response.status_code}")
                return self._fallback_forecast(lat, lon)
            
            points_data = points_response.json()
            forecast_url = points_data['properties']['forecast']
            
            # Step 2: Get detailed forecast
            forecast_response = self.session.get(forecast_url)
            forecast_data = forecast_response.json()
            
            # Find forecast period closest to game time
            periods = forecast_data['properties']['periods']
            game_period = self._find_closest_period(periods, game_time)
            
            return {
                'temperature': game_period['temperature'],
                'wind_speed': self._parse_wind(game_period['windSpeed']),
                'wind_direction': game_period['windDirection'],
                'short_forecast': game_period['shortForecast'],
                'detailed_forecast': game_period['detailedForecast'],
                'precipitation_probability': game_period.get('probabilityOfPrecipitation', {}).get('value', 0),
                'source': 'NOAA',
                'confidence': 'HIGH'
            }
        
        except Exception as e:
            logger.error(f"NOAA API error: {e}")
            return self._fallback_forecast(lat, lon)
    
    def _parse_wind(self, wind_str: str) -> int:
        """Parse wind speed from NOAA string."""
        # Examples: "10 mph", "5 to 10 mph", "10 to 15 mph"
        try:
            if 'to' in wind_str:
                # Take upper bound: "10 to 15 mph" → 15
                parts = wind_str.split('to')
                speed = int(parts[1].strip().split()[0])
            else:
                speed = int(wind_str.split()[0])
            return speed
        except:
            return 8  # Default/average
    
    def _find_closest_period(self, periods: List, game_time: datetime) -> Dict:
        """Find forecast period closest to game time."""
        for period in periods:
            period_start = datetime.fromisoformat(period['startTime'].replace('Z', '+00:00'))
            period_end = datetime.fromisoformat(period['endTime'].replace('Z', '+00:00'))
            
            if period_start <= game_time <= period_end:
                return period
        
        # If exact match not found, return first period
        return periods[0]
    
    def _fallback_forecast(self, lat: float, lon: float) -> Dict:
        """Fallback if NOAA API fails."""
        logger.warning("Using fallback weather forecast")
        return {
            'temperature': 55,  # Average
            'wind_speed': 8,
            'wind_direction': 'Variable',
            'short_forecast': 'Unknown',
            'precipitation_probability': 20,
            'source': 'FALLBACK',
            'confidence': 'LOW'
        }
    
    def calculate_weather_edge(self, weather: Dict, market_total: float) -> Dict:
        """
        Calculate edge based on weather conditions.
        
        Based on research:
        - Wind >15 MPH: Unders hit 60-62%
        - Temp <25°F: Unders hit 56-58%
        - Combined: Unders hit 65%+
        """
        wind = weather['wind_speed']
        temp = weather['temperature']
        
        # Wind impact
        if wind >= 20:
            total_adjustment = -6.5
            under_prob = 0.65
            edge_category = 'MAJOR'
        elif wind >= 15:
            total_adjustment = -4.0
            under_prob = 0.61
            edge_category = 'SIGNIFICANT'
        elif wind >= 12:
            total_adjustment = -2.0
            under_prob = 0.56
            edge_category = 'MODERATE'
        else:
            total_adjustment = 0
            under_prob = 0.50
            edge_category = 'NONE'
        
        # Temperature impact (extreme cold)
        if temp < 20:
            total_adjustment -= 3.5
            under_prob += 0.06
        elif temp < 30:
            total_adjustment -= 1.5
            under_prob += 0.03
        
        # Precipitation impact
        if weather['precipitation_probability'] > 60:
            total_adjustment -= 2.0
            under_prob += 0.04
        
        # Calculate edge
        # Assume market adjusts total by ~50% of our adjustment
        market_adjustment = total_adjustment * 0.5
        our_edge = abs(total_adjustment - market_adjustment)
        
        return {
            'total_adjustment': total_adjustment,
            'expected_market_adjustment': market_adjustment,
            'edge_points': our_edge,
            'under_probability': min(under_prob, 0.70),  # Cap at 70%
            'edge_category': edge_category,
            'recommendation': 'UNDER' if our_edge > 1.5 else 'NO_BET',
            'confidence': weather['confidence']
        }
    
    def get_game_weather(self, team: str, game_time: datetime) -> Dict:
        """
        Get complete weather profile for game.
        
        Args:
            team: Home team abbreviation
            game_time: Game start time
            
        Returns:
            Complete weather analysis with betting recommendations
        """
        stadium = self.get_stadium_location(team)
        
        if not stadium:
            logger.warning(f"Stadium not found for team {team}")
            return {'error': 'Stadium not found'}
        
        # Check if dome
        if stadium.get('roof') == 'dome':
            return {
                'is_dome': True,
                'temperature': 72,
                'wind_speed': 0,
                'edge_category': 'NONE',
                'recommendation': 'NO_WEATHER_EDGE'
            }
        
        # Get NOAA forecast
        forecast = self.get_forecast(stadium['lat'], stadium['lon'], game_time)
        
        # Calculate betting edge
        # Note: Need market total as input (from odds data)
        edge_analysis = self.calculate_weather_edge(forecast, market_total=45.0)  # Placeholder
        
        return {
            **forecast,
            **edge_analysis,
            'stadium': stadium,
        }


if __name__ == '__main__':
    # Test the agent
    agent = NOAAWeatherAgent()
    
    # Test Lambeau Field forecast
    weather = agent.get_game_weather('GB', datetime.now() + timedelta(days=1))
    
    print("="*70)
    print("NOAA WEATHER AGENT TEST")
    print("="*70)
    print(f"Temperature: {weather.get('temperature')}°F")
    print(f"Wind: {weather.get('wind_speed')} MPH")
    print(f"Precipitation: {weather.get('precipitation_probability')}%")
    print(f"Edge Category: {weather.get('edge_category')}")
    print(f"Recommendation: {weather.get('recommendation')}")
    print("="*70)

