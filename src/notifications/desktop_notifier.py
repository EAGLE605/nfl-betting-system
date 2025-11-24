"""
Desktop notification sender for Windows.

Sends system tray notifications for immediate alerts.
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class DesktopNotifier:
    """Sends desktop notifications (Windows toast notifications)."""
    
    def __init__(self):
        """Initialize desktop notifier."""
        # Try to import plyer (optional dependency)
        try:
            from plyer import notification
            self.notification = notification
            self.enabled = True
        except ImportError:
            logger.warning("Plyer not installed - desktop notifications disabled")
            self.enabled = False
    
    def send_toast(self, analysis: Dict, parlays: Dict) -> bool:
        """
        Send Windows toast notification.
        
        Args:
            analysis: Pre-game analysis results
            parlays: Parlay recommendations
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("Desktop notifier not enabled (plyer not installed)")
            return False
        
        try:
            recommendations = analysis.get('recommendations', [])
            game_info = analysis['game_info']
            
            if not recommendations:
                return False
            
            num_bets = len(recommendations)
            num_parlays = len(parlays.get('2_leg', [])) + len(parlays.get('3_leg', []))
            
            # Create notification
            title = f"🏈 NFL Bets Available"
            message = (
                f"{game_info['away_team']} @ {game_info['home_team']}\n"
                f"{num_bets} singles, {num_parlays} parlays"
            )
            
            self.notification.notify(
                title=title,
                message=message,
                app_name="NFL Betting System",
                timeout=10  # 10 seconds
            )
            
            logger.info("Desktop notification sent")
            return True
            
        except Exception as e:
            logger.error(f"Error sending desktop notification: {e}")
            return False

