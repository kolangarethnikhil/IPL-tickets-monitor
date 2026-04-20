"""
Telegram Bot Notifier
Sends alerts and heartbeat messages
"""

import requests
import json
from datetime import datetime
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str = None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, text: str, chat_id: str = None, parse_mode: str = "HTML") -> bool:
        """Send a message to Telegram"""
        try:
            target_chat_id = chat_id or self.chat_id
            
            if not target_chat_id:
                logger.error("No chat_id provided")
                return False
            
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': target_chat_id,
                'text': text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': False
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Message sent to {target_chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def send_ticket_alert(self, match: Dict, chat_id: str = None) -> bool:
        """Send ticket availability alert"""
        status_emoji = {
            'AVAILABLE': '🚨',
            'COMING_SOON': '🔔',
            'SOLD_OUT': '❌',
            'NOT_YET_ANNOUNCED': '📅'
        }
        
        emoji = status_emoji.get(match['status'], '⚡')
        
        message = f"""
{emoji} <b>IPL TICKET ALERT!</b> {emoji}

<b>🏏 Match:</b> {match['teams']}
<b>📅 Date:</b> {match['date']} at {match['time']}
<b>🏟️ Stadium:</b> {match['stadium']}
<b>⚡ Status:</b> {match['status'].replace('_', ' ')}
"""
        
        if match['status'] == 'AVAILABLE' and match.get('booking_link'):
            message += f"\n<b>🎫 BOOK NOW:</b> {match['booking_link']}"
        
        message += f"\n\n<i>🕐 Checked at: {datetime.now().strftime('%I:%M %p')}</i>"
        
        return self.send_message(message, chat_id)
    
    def send_heartbeat(self, total_matches: int, active_monitors: int, chat_id: str = None) -> bool:
        """Send hourly heartbeat message"""
        message = f"""
✅ <b>Ticket Monitoring Active</b>

<b>📊 Status:</b>
- Monitoring {active_monitors} match(es)
- Total matches found: {total_matches}
- Last check: {datetime.now().strftime('%I:%M %p, %d %b')}

<b>⏱️ Next check:</b> Within 15 minutes

<i>You'll get instant alerts when tickets are available!</i>
"""
        return self.send_message(message, chat_id)
    
    def send_status_change_alert(self, match: Dict, old_status: str, new_status: str, chat_id: str = None) -> bool:
        """Alert when ticket status changes"""
        message = f"""
🔔 <b>STATUS CHANGE DETECTED!</b>

<b>🏏 Match:</b> {match['teams']}
<b>📅 Date:</b> {match['date']}

<b>Old Status:</b> {old_status.replace('_', ' ')}
<b>New Status:</b> {new_status.replace('_', ' ')} ⚡

"""
        
        if new_status == 'AVAILABLE':
            message += f"<b>🎫 BOOK NOW:</b> {match.get('booking_link', 'Check District.in')}"
        elif new_status == 'COMING_SOON':
            message += "Sale will start soon! Keep this chat open for instant alerts."
        
        return self.send_message(message, chat_id)
    
    def send_welcome_message(self, user_preferences: Dict, chat_id: str = None) -> bool:
        """Send welcome message when monitoring starts"""
        message = f"""
🎉 <b>Welcome to IPL Ticket Alert!</b>

✅ <b>Monitoring Activated</b>

<b>Your Preferences:</b>
"""
        
        if user_preferences.get('team'):
            message += f"• Team: {user_preferences['team']}\n"
        
        if user_preferences.get('city'):
            message += f"• City: {user_preferences['city']}\n"
        
        if user_preferences.get('max_price'):
            message += f"• Max Price: ₹{user_preferences['max_price']}\n"
        
        message += """

<b>⚡ What happens next:</b>
- We check District.in every 15 minutes
- You'll get instant alerts when tickets go live
- Hourly heartbeat to confirm monitoring is active

<i>Sit back and relax - we've got you covered! 🏏</i>
"""
        
        return self.send_message(message, chat_id)
