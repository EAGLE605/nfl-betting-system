# 🎯 COMPOSER TASK PROD-003: Notification System

**Priority**: HIGH  
**Estimated Time**: 2-3 hours  
**Dependencies**: PROD-001, PROD-002  
**Status**: NOT STARTED

---

## 📋 **OBJECTIVE**

Build a multi-channel notification system that sends bet recommendations via:
1. **Email** (detailed HTML format with all analysis)
2. **SMS** (quick text alert with top picks) - OPTIONAL
3. **Desktop** (Windows notification for immediate alerts) - OPTIONAL

The system should be modular, allowing users to enable/disable channels independently.

---

## 📁 **FILES TO CREATE**

### **Main File**:
**Path**: `scripts/send_bet_notifications.py`  
**Size**: ~500-600 lines

### **Supporting Module**:
**Path**: `src/notifications/__init__.py`  
**Path**: `src/notifications/email_sender.py`  
**Path**: `src/notifications/sms_sender.py`  
**Path**: `src/notifications/desktop_notifier.py`

---

## 🔧 **DETAILED REQUIREMENTS**

### **1. EMAIL SENDER MODULE**

**File**: `src/notifications/email_sender.py`

```python
"""
Email notification sender using Gmail SMTP.

Sends detailed HTML-formatted bet recommendations via email.
"""

import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List

logger = logging.getLogger(__name__)


class EmailSender:
    """Sends email notifications via Gmail SMTP."""
    
    def __init__(self, smtp_user: str, smtp_password: str, recipient: str):
        """
        Initialize email sender.
        
        Args:
            smtp_user: Gmail address (e.g., yourname@gmail.com)
            smtp_password: Gmail app password (NOT regular password!)
            recipient: Email address to send notifications to
            
        Note:
            Gmail app passwords: https://support.google.com/accounts/answer/185833
        """
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.recipient = recipient
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 465  # SSL port
    
    def send_bet_alert(self, analysis: Dict, parlays: Dict) -> bool:
        """
        Send bet alert email with recommendations.
        
        Args:
            analysis: Pre-game analysis results (from PROD-001)
            parlays: Parlay recommendations (from PROD-002)
        
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = self._create_subject(analysis, parlays)
            msg['From'] = self.smtp_user
            msg['To'] = self.recipient
            
            # Create HTML body
            html_body = self._create_html_body(analysis, parlays)
            
            # Attach HTML
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Send via Gmail SMTP
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {self.recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def _create_subject(self, analysis: Dict, parlays: Dict) -> str:
        """Create email subject line."""
        num_bets = len(analysis.get('recommendations', []))
        num_parlays = len(parlays.get('2_leg', [])) + len(parlays.get('3_leg', []))
        
        if num_bets == 0 and num_parlays == 0:
            return "🏈 NFL Bets: No Recommendations Today"
        
        subject = f"🏈 NFL Bets: {num_bets} Singles"
        if num_parlays > 0:
            subject += f", {num_parlays} Parlays"
        
        return subject
    
    def _create_html_body(self, analysis: Dict, parlays: Dict) -> str:
        """
        Create HTML email body.
        
        Returns:
            HTML string with styled bet recommendations
        """
        # Get game info
        game_info = analysis['game_info']
        recommendations = analysis.get('recommendations', [])
        matching_edges = analysis.get('matching_edges', [])
        
        html = f"""
        <html>
          <head>
            <style>
              body {{
                font-family: Arial, sans-serif;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
              }}
              .header {{
                background: #1a1a2e;
                color: white;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
              }}
              .game-title {{
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 10px;
              }}
              .game-time {{
                font-size: 14px;
                opacity: 0.8;
              }}
              .section {{
                background: #f5f5f5;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
              }}
              .section-title {{
                font-size: 18px;
                font-weight: bold;
                color: #1a1a2e;
                margin-bottom: 10px;
                border-bottom: 2px solid #4CAF50;
                padding-bottom: 5px;
              }}
              .bet-card {{
                background: white;
                padding: 15px;
                border-left: 4px solid #4CAF50;
                margin-bottom: 10px;
                border-radius: 4px;
              }}
              .bet-title {{
                font-size: 16px;
                font-weight: bold;
                color: #4CAF50;
                margin-bottom: 8px;
              }}
              .bet-detail {{
                font-size: 14px;
                margin: 4px 0;
              }}
              .edge-badge {{
                display: inline-block;
                background: #2196F3;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                margin-top: 8px;
              }}
              .tier-s {{
                background: #FFD700;
                color: #333;
                padding: 2px 6px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 11px;
              }}
              .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                font-size: 12px;
                color: #666;
                text-align: center;
              }}
            </style>
          </head>
          <body>
            <div class="header">
              <div class="game-title">
                🏈 {game_info['away_team']} @ {game_info['home_team']}
              </div>
              <div class="game-time">
                Week {game_info.get('week', 'N/A')} • {game_info.get('kickoff_str', 'TBD')}
              </div>
            </div>
        """
        
        # Single bets section
        if recommendations:
            html += """
            <div class="section">
              <div class="section-title">💰 Single Bet Recommendations</div>
            """
            
            for rec in recommendations:
                html += f"""
              <div class="bet-card">
                <div class="bet-title">
                  {rec['team']} {rec['bet_type'].upper()}
                  <span class="tier-s">TIER {rec['confidence_tier']}</span>
                </div>
                <div class="bet-detail"><strong>Odds:</strong> {rec['odds']:+.0f} ({rec['sportsbook']})</div>
                <div class="bet-detail"><strong>Win Probability:</strong> {rec['win_probability']:.1%}</div>
                <div class="bet-detail"><strong>Expected Value:</strong> {rec['expected_value']:+.1%}</div>
                <div class="bet-detail"><strong>Kelly Fraction:</strong> {rec['kelly_fraction']:.2%} of bankroll</div>
                <span class="edge-badge">{rec['edge_name']}</span>
              </div>
                """
            
            html += "</div>"
        
        # Parlays section
        if parlays.get('2_leg') or parlays.get('3_leg'):
            html += """
            <div class="section">
              <div class="section-title">🎲 Parlay Recommendations</div>
            """
            
            # 2-leg parlays
            for i, parlay in enumerate(parlays.get('2_leg', [])[:3], 1):
                html += f"""
              <div class="bet-card">
                <div class="bet-title">2-Leg Parlay #{i}</div>
                """
                
                for j, leg in enumerate(parlay['legs'], 1):
                    html += f"""
                <div class="bet-detail">
                  <strong>Leg {j}:</strong> {leg['team']} {leg['bet_type']} ({leg['odds']:+.0f})
                  <br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{leg['game']}
                </div>
                    """
                
                html += f"""
                <div class="bet-detail"><strong>Combined Odds:</strong> {parlay['parlay_odds']:+.0f}</div>
                <div class="bet-detail"><strong>Win Probability:</strong> {parlay['combined_probability']:.1%}</div>
                <div class="bet-detail"><strong>Expected ROI:</strong> {parlay['expected_roi']:+.1%}</div>
              </div>
                """
            
            html += "</div>"
        
        # Matching edges section
        if matching_edges:
            html += """
            <div class="section">
              <div class="section-title">✅ Discovered Edges</div>
            """
            
            for edge in matching_edges:
                html += f"""
              <div class="bet-detail">
                <strong>{edge['edge_name']}</strong>: 
                {edge['win_rate']:.1%} WR, {edge['roi']:+.1%} ROI 
                ({edge['sample_size']} games)
              </div>
                """
            
            html += "</div>"
        
        # Footer
        html += """
            <div class="footer">
              ⚠️ This is a research tool. Bet responsibly.<br>
              Generated by NFL Betting System • {datetime.now().strftime('%Y-%m-%d %I:%M %p')}
            </div>
          </body>
        </html>
        """.format(datetime=datetime)
        
        return html
```

---

### **2. SMS SENDER MODULE** (OPTIONAL)

**File**: `src/notifications/sms_sender.py`

```python
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
            message = (
                f"🏈 NFL BET:\n"
                f"{game_info['away_team']} @ {game_info['home_team']}\n"
                f"BET: {top_bet['team']} {top_bet['bet_type']}\n"
                f"Odds: {top_bet['odds']:+.0f} | EV: {top_bet['expected_value']:+.0%}\n"
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
```

---

### **3. DESKTOP NOTIFIER MODULE** (OPTIONAL)

**File**: `src/notifications/desktop_notifier.py`

```python
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
```

---

### **4. MAIN NOTIFICATION SCRIPT**

**File**: `scripts/send_bet_notifications.py`

```python
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

from src.notifications.email_sender import EmailSender
from src.notifications.sms_sender import SMSSender
from src.notifications.desktop_notifier import DesktopNotifier

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
    
    # Initialize manager
    manager = NotificationManager()
    
    # Send notifications
    results = manager.send_all_notifications(args.analysis, args.parlays)
    
    # Print results
    print(f"\n{'='*80}")
    print("NOTIFICATION RESULTS")
    print(f"{'='*80}")
    for channel, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"{channel.upper()}: {status}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
```

---

## ✅ **ACCEPTANCE CRITERIA**

### **MUST HAVE**:
1. ✅ Email notifications work with Gmail SMTP
2. ✅ HTML formatting is clean and professional
3. ✅ Handles missing credentials gracefully
4. ✅ Loads analysis and parlay data correctly
5. ✅ Only sends notifications for games with recommendations
6. ✅ Logs all actions
7. ✅ Returns success/failure status

### **OPTIONAL** (Nice to Have):
1. SMS notifications via Twilio
2. Desktop toast notifications (Windows)
3. Multiple game alerts in single email

### **TESTING REQUIREMENTS**:
1. Test email sending with valid credentials
2. Test email with missing credentials (should skip gracefully)
3. Test HTML rendering (open in browser)
4. Test with zero recommendations (should skip)
5. Test with multiple games
6. Verify SMS works (if Twilio configured)
7. Verify desktop notification appears

---

## 📝 **ENVIRONMENT VARIABLES NEEDED**

Add to `config/api_keys.env`:

```bash
# Email notifications (required)
EMAIL_USER="your_email@gmail.com"
EMAIL_PASSWORD="your_gmail_app_password"
EMAIL_RECIPIENT="recipient@email.com"

# SMS notifications (optional)
TWILIO_ACCOUNT_SID="your_twilio_sid"
TWILIO_AUTH_TOKEN="your_twilio_token"
TWILIO_PHONE_FROM="+1234567890"
TWILIO_PHONE_TO="+1234567890"
```

**Gmail App Password**: https://support.google.com/accounts/answer/185833

---

## 🚀 **EXECUTION COMMAND**

```bash
# Set environment variables first
export EMAIL_USER="your_email@gmail.com"
export EMAIL_PASSWORD="your_app_password"
export EMAIL_RECIPIENT="recipient@email.com"

# Send notifications
python scripts/send_bet_notifications.py \
  --analysis reports/pregame_analysis.json \
  --parlays reports/parlays.json
```

---

**STATUS**: Ready for Composer 1 to implement  
**PRIORITY**: HIGH  
**DEPENDS ON**: PROD-001, PROD-002 (needs their JSON outputs)

