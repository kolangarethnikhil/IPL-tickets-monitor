"""
District.in IPL Ticket Scraper
Monitors ticket availability and status changes
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time
import re
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DistrictIPLScraper:
    def __init__(self):
        self.base_url = "https://www.district.in/events/ipl-ticket-booking"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        
    def scrape_all_matches(self) -> List[Dict]:
        """Scrape all IPL matches from District.in"""
        try:
            logger.info(f"Scraping District.in: {self.base_url}")
            response = requests.get(self.base_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            matches = []
            
            match_cards = soup.find_all('div', class_=re.compile(r'card|event|match', re.I))
            
            if not match_cards:
                match_cards = soup.find_all(['div', 'article'], recursive=True)
            
            logger.info(f"Found {len(match_cards)} potential match cards")
            
            for card in match_cards:
                try:
                    match_data = self._parse_match_card(card)
                    if match_data and match_data.get('teams'):
                        matches.append(match_data)
                except Exception as e:
                    continue
            
            logger.info(f"Successfully parsed {len(matches)} matches")
            return matches
            
        except Exception as e:
            logger.error(f"Error scraping District.in: {e}")
            return []
    
    def _parse_match_card(self, card) -> Optional[Dict]:
        """Parse individual match card"""
        try:
            teams_text = card.get_text()
            
            team_patterns = [
                'Chennai Super Kings', 'CSK',
                'Mumbai Indians', 'MI',
                'Royal Challengers Bangalore', 'RCB',
                'Kolkata Knight Riders', 'KKR',
                'Delhi Capitals', 'DC',
                'Rajasthan Royals', 'RR',
                'Punjab Kings', 'PBKS',
                'Sunrisers Hyderabad', 'SRH',
                'Gujarat Titans', 'GT',
                'Lucknow Super Giants', 'LSG'
            ]
            
            found_teams = []
            for pattern in team_patterns:
                if pattern in teams_text:
                    found_teams.append(pattern)
            
            if len(found_teams) < 2:
                return None
            
            teams = ' vs '.join(found_teams[:2])
            
            date_elem = card.find(text=re.compile(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', re.I))
            date = date_elem.strip() if date_elem else "Date TBD"
            
            stadium_elem = card.find(text=re.compile(r'Stadium|Cricket|Ground', re.I))
            stadium = stadium_elem.strip() if stadium_elem else "Stadium TBD"
            
            time_elem = card.find(text=re.compile(r'\d+:\d+\s*(AM|PM)', re.I))
            match_time = time_elem.strip() if time_elem else "Time TBD"
            
            status = self._detect_status(card)
            
            book_link = None
            book_btn = card.find('a', text=re.compile(r'Book tickets', re.I))
            if book_btn and book_btn.get('href'):
                book_link = book_btn['href']
                if not book_link.startswith('http'):
                    book_link = f"https://www.district.in{book_link}"
            
            return {
                'teams': teams,
                'date': date,
                'stadium': stadium,
                'time': match_time,
                'status': status,
                'booking_link': book_link,
                'timestamp': datetime.now().isoformat(),
                'source': 'district.in'
            }
            
        except:
            return None
    
    def _detect_status(self, card) -> str:
        """Detect ticket status"""
        card_text = card.get_text().lower()
        
        if 'sale is live' in card_text or 'book tickets' in card_text:
            return 'AVAILABLE'
        elif 'sale starts soon' in card_text or 'notify me' in card_text:
            return 'COMING_SOON'
        elif 'coming soon' in card_text:
            return 'NOT_YET_ANNOUNCED'
        elif 'sold out' in card_text:
            return 'SOLD_OUT'
        else:
            return 'UNKNOWN'
    
    def filter_matches(self, matches: List[Dict], team: str = None, city: str = None) -> List[Dict]:
        """Filter matches by team or city"""
        filtered = matches
        
        if team and team.lower() != 'any':
            filtered = [m for m in filtered if team.lower() in m['teams'].lower()]
        
        if city and city.lower() != 'any':
            filtered = [m for m in filtered if city.lower() in m['stadium'].lower()]
        
        return filtered
    
    def save_results(self, matches: List[Dict], filepath: str = "data/tickets.json"):
        """Save results"""
        try:
            with open(filepath, 'w') as f:
                json.dump({
                    'last_updated': datetime.now().isoformat(),
                    'total_matches': len(matches),
                    'matches': matches
                }, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving: {e}")
            return False
