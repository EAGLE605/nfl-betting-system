"""
Notification modules for NFL betting system.

Supports multiple notification channels:
- Email (Gmail SMTP)
- SMS (Twilio) - optional
- Desktop (Windows toast) - optional
"""

from .desktop_notifier import DesktopNotifier
from .email_sender import EmailSender
from .sms_sender import SMSSender

__all__ = ['EmailSender', 'SMSSender', 'DesktopNotifier']

