"""
Main IPL Ticket Monitor
Orchestrates scraping, change detection, and notifications
"""

import os
import json
from datetime import datetime
from typing import Dict, List
import logging
from scraper import DistrictIPLScraper
from notifier import TelegramNotifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IPLTicketMonitor:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '8788246277:AAHR3bz6IAIak23n_UYZdBWhpNeii8_4puE')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
        
        self.scraper = DistrictIPLScraper()
        self.notifier = TelegramNotifier(self.bot_token, self.chat_id)
        
        self.data_file = "data/tickets.json"
        self.config_file = "data/user_config.json"
        
    def load_previous_data(self) -> Dict:
        """Load previous scraping results"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            return {'matches': []}
        except Exception as e:
            logger.error(f"Error loading previous data: {e}")
            return {'matches': []}
    
    def load_user_preferences(self) -> Dict:
        """Load user preferences from file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def detect_changes(self, old_matches: List[Dict], new_matches: List[Dict]) -> Dict:
        """Detect status changes"""
        changes = {
            'status_changes': [],
            'new_available': []
        }
        
        old_lookup = {f"{m['teams']}_{m['date']}": m for m in old_matches}
        
        for new_match in new_matches:
            match_key = f"{new_match['teams']}_{new_match['date']}"
            old_match = old_lookup.get(match_key)
            
            if old_match:
                if old_match['status'] != new_match['status']:
                    changes['status_changes'].append({
                        'match': new_match,
                        'old_status': old_match['status'],
                        'new_status': new_match['status']
                    })
                    
                    if new_match['status'] == 'AVAILABLE':
                        changes['new_available'].append(new_match)
            else:
                if new_match['status'] == 'AVAILABLE':
                    changes['new_available'].append(new_match)
        
        return changes
    
    def apply_user_filters(self, matches: List[Dict]) -> List[Dict]:
        """Apply user preferences to filter matches"""
        try:
            prefs = self.load_user_preferences()
            
            team = prefs.get('team', 'any')
            city = prefs.get('city', 'any')
            
            filtered = self.scraper.filter_matches(matches, team, city)
            
            return filtered
            
        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            return matches
    
    def run_check(self, send_alerts: bool = True):
        """Run a single monitoring check"""
        logger.info("=" * 60)
        logger.info(f"Starting check at {datetime.now().strftime('%I:%M %p')}")
        logger.info("=" * 60)
        
        previous_data = self.load_previous_data()
        old_matches = previous_data.get('matches', [])
        
        logger.info("Scraping District.in...")
        all_matches = self.scraper.scrape_all_matches()
        
        if not all_matches:
            logger.warning("No matches found!")
            return
        
        logger.info(f"Found {len(all_matches)} total matches")
        
        filtered_matches = self.apply_user_filters(all_matches)
        logger.info(f"After filters: {len(filtered_matches)} matches")
        
        changes = self.detect_changes(old_matches, filtered_matches)
        
        if send_alerts and self.chat_id:
            for change in changes['status_changes']:
                logger.info(f"Status change: {change['match']['teams']} - {change['old_status']} → {change['new_status']}")
                self.notifier.send_status_change_alert(
                    change['match'],
                    change['old_status'],
                    change['new_status']
                )
            
            for match in changes['new_available']:
                logger.info(f"🚨 TICKETS AVAILABLE: {match['teams']}")
                self.notifier.send_ticket_alert(match)
        
        self.scraper.save_results(all_matches, self.data_file)
        
        logger.info(f"\nCheck complete:")
        logger.info(f"  • Total matches: {len(all_matches)}")
        logger.info(f"  • Monitored matches: {len(filtered_matches)}")
        logger.info(f"  • Status changes: {len(changes['status_changes'])}")
        logger.info(f"  • New available: {len(changes['new_available'])}")
    
    def send_heartbeat(self):
        """Send hourly heartbeat message"""
        try:
            data = self.load_previous_data()
            prefs = self.load_user_preferences()
            
            total_matches = data.get('total_matches', 0)
            
            team = prefs.get('team', 'any')
            city = prefs.get('city', 'any')
            
            monitored = len(self.scraper.filter_matches(data.get('matches', []), team, city))
            
            if self.chat_id:
                self.notifier.send_heartbeat(total_matches, monitored)
                logger.info("Heartbeat sent")
        
        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")


def main():
    """Main entry point"""
    import sys
    
    monitor = IPLTicketMonitor()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "heartbeat":
            monitor.send_heartbeat()
        elif command == "check":
            monitor.run_check(send_alerts=True)
        else:
            print(f"Unknown command: {command}")
    else:
        monitor.run_check(send_alerts=True)


if __name__ == "__main__":
    main()
