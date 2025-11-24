"""
SMS notification sender using Twilio.

Sends quick text alerts with top bet recommendations.
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class SMSSender:
    """Sends SMS notifications via Twilio."""
    
    def __init__(self, account_sid: str, auth_token: str, from_phone: str, to_phone: str):
        """
        Initialize SMS sender.
        
        Args:
            account_sid: Twilio account SID
            auth_token: Twilio auth token
            from_phone: Twilio phone number (e.g., +1234567890)
            to_phone: Your phone number to receive alerts
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_phone = from_phone
        self.to_phone = to_phone
        
        # Try to import Twilio (optional dependency)
        try:
            from twilio.rest import Client
            self.client = Client(account_sid, auth_token)
            self.enabled = True
        except ImportError:
            logger.warning("Twilio not installed - SMS notifications disabled")
            self.enabled = False
    
    def send_quick_alert(self, analysis: Dict, parlays: Dict) -> bool:
        """
        Send quick SMS alert with top recommendation.
        
        Args:
            analysis: Pre-game analysis results
            parlays: Parlay recommendations
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("SMS sender not enabled (Twilio not installed)")
            return False
        
        try:
            # Get top recommendation
            recommendations = analysis.get('recommendations', [])
            game_info = analysis['game_info']
            
            if not recommendations:
                return False  # No bets, no SMS
            
            top_bet = recommendations[0]
            
            # Create message (160 chars max for single SMS)
            odds_str = f"{top_bet['odds']:+.0f}" if top_bet['odds'] else "N/A"
            ev_str = f"{top_bet['expected_value']:+.0%}" if top_bet['expected_value'] else "N/A"
            
            message = (
                f"🏈 NFL BET:\n"
                f"{game_info['away_team']} @ {game_info['home_team']}\n"
                f"BET: {top_bet['team']} {top_bet['bet_type']}\n"
                f"Odds: {odds_str} | EV: {ev_str}\n"
                f"Tier {top_bet['confidence_tier']}"
            )
            
            # Send SMS
            self.client.messages.create(
                body=message,
                from_=self.from_phone,
                to=self.to_phone
            )
            
            logger.info(f"SMS sent successfully to {self.to_phone}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return False

