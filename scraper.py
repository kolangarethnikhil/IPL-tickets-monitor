import requests
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# BMS internal API headers (mimics the mobile app)
BMS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://in.bookmyshow.com/",
    "Origin": "https://in.bookmyshow.com",
}

# BMS city codes
CITY_CODES = {
    "bangalore": "BLR",
    "mumbai": "MUMBAI",
    "delhi": "NCR",
    "chennai": "CHEN",
    "kolkata": "KOLKATA",
    "hyderabad": "HYD",
    "pune": "PUNE",
    "ahmedabad": "AHM",
    "jaipur": "JAIPUR",
    "lucknow": "LUCK",
}


@dataclass
class MatchInfo:
    event_code: str
    name: str
    venue: str
    date: str
    availability: str  # "Available", "Filling Fast", "Sold Out", "Not Open Yet"
    booking_url: str
    city: str


def fetch_ipl_events(city: str) -> list[MatchInfo]:
    """
    Fetches IPL events from BookMyShow's internal explore API.
    Returns a list of MatchInfo objects.
    """
    city_lower = city.lower()
    region_code = CITY_CODES.get(city_lower, city_lower.upper())

    url = "https://in.bookmyshow.com/api/explore/v1/lists/events"
    params = {
        "appCode": "MOBAND2",
        "appVersion": "14430",
        "language": "en",
        "regionCode": region_code,
        "subCategory": "Cricket",
        "category": "SPORTS",
        "pageNumber": "0",
        "pageSize": "10",
        "filterFields": "",
        "latitude": "",
        "longitude": "",
        "userAgent": BMS_HEADERS["User-Agent"],
        "platform": "Desktop",
    }

    try:
        response = requests.get(url, headers=BMS_HEADERS, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch events for {city}: {e}")
        return []
    except ValueError:
        logger.error(f"Invalid JSON response for {city}")
        return []

    matches = []
    event_list = data.get("BookMyShow", {}).get("arrEvent", []) or \
                 data.get("arrEvent", []) or \
                 data.get("ResultSet", {}).get("Result", []) or []

    for event in event_list:
        try:
            event_code = event.get("EventCode", "")
            name = event.get("EventTitle", event.get("EventName", "Unknown Match"))

            # Filter for IPL events only
            if not any(kw in name.upper() for kw in ["IPL", "VS", " V ", "RCB", "CSK", "MI ", "KKR", "SRH", "DC ", "PBKS", "RR ", "GT ", "LSG"]):
                continue

            venue = event.get("VenueName", "TBD")
            date = event.get("EventDate", event.get("ShowDate", "TBD"))
            availability = _parse_availability(event)
            booking_url = f"https://in.bookmyshow.com/events/{event_code.lower()}"

            matches.append(MatchInfo(
                event_code=event_code,
                name=name,
                venue=venue,
                date=date,
                availability=availability,
                booking_url=booking_url,
                city=city.capitalize(),
            ))
        except (KeyError, TypeError) as e:
            logger.warning(f"Skipping malformed event entry: {e}")
            continue

    logger.info(f"Found {len(matches)} IPL events for {city}")
    return matches


def _parse_availability(event: dict) -> str:
    """Parses availability status from an event dict."""
    status = event.get("AvailableSeatsStatus", event.get("SeatAvailability", "")).upper()
    if "SOLD" in status or status == "0":
        return "Sold Out"
    elif "FILLING" in status or "FAST" in status:
        return "Filling Fast"
    elif "AVAILABLE" in status or status == "1":
        return "Available"
    elif "OPEN" not in status and not status:
        # Check if there's a booking open flag
        is_open = event.get("IsBookingOpen", event.get("BookingOpen", False))
        if not is_open:
            return "Not Open Yet"
    return "Available"


def check_ticket_availability(city: str) -> list[MatchInfo]:
    """
    Main function to call from the alert loop.
    Returns only matches where tickets ARE available or filling fast.
    """
    all_matches = fetch_ipl_events(city)
    available = [m for m in all_matches if m.availability in ("Available", "Filling Fast")]
    return available


def get_all_matches(city: str) -> list[MatchInfo]:
    """Returns all IPL matches regardless of availability — useful for status summaries."""
    return fetch_ipl_events(city)
