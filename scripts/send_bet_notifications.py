"""
Bet Notification Sender

Sends bet recommendations via multiple channels:
- Email (detailed HTML)
- SMS (quick alert) - optional
- Desktop (toast notification) - optional

Usage:
    python scripts/send_bet_notifications.py --analysis reports/pregame_analysis.json --parlays reports/parlays.json
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import logging
import os
from typing import Dict, List

from src.notifications.desktop_notifier import DesktopNotifier
from src.notifications.email_sender import EmailSender
from src.notifications.sms_sender import SMSSender

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NotificationManager:
    """Manages all notification channels."""
    
    def __init__(self):
        """Initialize notification manager."""
        # Load credentials from environment
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.email_recipient = os.getenv('EMAIL_RECIPIENT')
        
        self.twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_from = os.getenv('TWILIO_PHONE_FROM')
        self.twilio_to = os.getenv('TWILIO_PHONE_TO')
        
        # Initialize senders
        self.email_sender = None
        self.sms_sender = None
        self.desktop_notifier = DesktopNotifier()
        
        # Set up email if credentials available
        if all([self.email_user, self.email_password, self.email_recipient]):
            self.email_sender = EmailSender(
                self.email_user,
                self.email_password,
                self.email_recipient
            )
            logger.info("Email sender initialized")
        else:
            logger.warning("Email credentials not set - email notifications disabled")
        
        # Set up SMS if credentials available
        if all([self.twilio_sid, self.twilio_token, self.twilio_from, self.twilio_to]):
            self.sms_sender = SMSSender(
                self.twilio_sid,
                self.twilio_token,
                self.twilio_from,
                self.twilio_to
            )
            logger.info("SMS sender initialized")
        else:
            logger.warning("Twilio credentials not set - SMS notifications disabled")
    
    def send_all_notifications(self, analysis_file: str, parlays_file: str) -> Dict[str, bool]:
        """
        Send notifications via all enabled channels.
        
        Args:
            analysis_file: Path to pregame analysis JSON
            parlays_file: Path to parlays JSON
        
        Returns:
            Dictionary of {channel: success_status}
        """
        # Load data
        with open(analysis_file, 'r') as f:
            analyses = json.load(f)
        
        with open(parlays_file, 'r') as f:
            parlays = json.load(f)
        
        results = {}
        
        # Send notifications for each game with recommendations
        for analysis in analyses:
            if not analysis.get('recommendations'):
                logger.info(f"No recommendations for {analysis['game_info']['away_team']} @ {analysis['game_info']['home_team']} - skipping")
                continue
            
            logger.info(f"\nSending notifications for {analysis['game_info']['away_team']} @ {analysis['game_info']['home_team']}")
            
            # Email
            if self.email_sender:
                results['email'] = self.email_sender.send_bet_alert(analysis, parlays)
            
            # SMS
            if self.sms_sender:
                results['sms'] = self.sms_sender.send_quick_alert(analysis, parlays)
            
            # Desktop
            if self.desktop_notifier:
                results['desktop'] = self.desktop_notifier.send_toast(analysis, parlays)
        
        return results


def main():
    """Main execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Send Bet Notifications')
    parser.add_argument('--analysis', required=True,
                       help='Path to pregame_analysis.json')
    parser.add_argument('--parlays', required=True,
                       help='Path to parlays.json')
    
    args = parser.parse_args()
    
    # Check files exist
    if not Path(args.analysis).exists():
        logger.error(f"Analysis file not found: {args.analysis}")
        return
    
    if not Path(args.parlays).exists():
        logger.error(f"Parlays file not found: {args.parlays}")
        return
    
    # Initialize manager
    manager = NotificationManager()
    
    # Send notifications
    results = manager.send_all_notifications(args.analysis, args.parlays)
    
    # Print results
    print(f"\n{'='*80}")
    print("NOTIFICATION RESULTS")
    print(f"{'='*80}")
    for channel, success in results.items():
        status = "[SUCCESS]" if success else "[FAILED]"
        print(f"{channel.upper()}: {status}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()

