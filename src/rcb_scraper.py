"""
RCB TicketGenie Scraper
-----------------------
Primary source for RCB home match tickets.
Hits the official RCB ticket API at rcbmpapi.ticketgenie.in
which powers shop.royalchallengers.com/ticket
"""

import requests
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

RCB_API_URL = "https://rcbmpapi.ticketgenie.in/ticket/eventlist/o"

# The RCB shop page that users land on — shown in alerts
RCB_SHOP_URL = "https://shop.royalchallengers.com/ticket"

# Mimic the headers the RCB website itself sends
RCB_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-IN,en-US;q=0.9,en;q=0.8",
    "Origin": "https://shop.royalchallengers.com",
    "Referer": "https://shop.royalchallengers.com/",
}


@dataclass
class RCBMatch:
    event_id: str
    name: str
    venue: str
    match_date: str          # raw string from API
    match_date_parsed: Optional[datetime]
    category: str            # e.g. "IPL 2025"
    availability: str        # "Available", "Sold Out", "Not Open Yet", "Unknown"
    booking_url: str
    raw: dict                # full raw event dict for debugging


def fetch_rcb_events() -> list[RCBMatch]:
    """
    Calls the RCB TicketGenie API and returns all listed events.
    Returns empty list (not exception) on failure so the alert loop keeps running.
    """
    try:
        response = requests.get(
            RCB_API_URL,
            headers=RCB_HEADERS,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"[RCB] Network error fetching events: {e}")
        return []
    except ValueError:
        logger.error("[RCB] Non-JSON response received")
        return []

    if data.get("status") != "Success":
        logger.warning(f"[RCB] API returned non-success status: {data.get('status')}")
        return []

    raw_events = data.get("result", [])

    if not raw_events:
        logger.info("[RCB] API returned 0 events (tickets not yet listed, or season gap)")
        return []

    matches = []
    for event in raw_events:
        try:
            match = _parse_event(event)
            matches.append(match)
        except Exception as e:
            logger.warning(f"[RCB] Failed to parse event: {e} | raw={event}")

    logger.info(f"[RCB] Found {len(matches)} events from TicketGenie API")
    return matches


def _parse_event(event: dict) -> RCBMatch:
    """Parses a single raw event dict from the TicketGenie API."""
    event_id = str(event.get("event_id", event.get("id", event.get("EventId", "unknown"))))
    name = event.get("event_name", event.get("name", event.get("EventName", "RCB Match")))
    venue = event.get("venue_name", event.get("venue", event.get("VenueName", "M. Chinnaswamy Stadium")))
    category = event.get("category", event.get("cat_name", "IPL 2025"))

    # Date parsing — TicketGenie may return various formats
    raw_date = (
        event.get("event_date") or
        event.get("start_date") or
        event.get("EventDate") or
        event.get("date") or
        "TBD"
    )
    parsed_date = _try_parse_date(raw_date)

    # Availability — check multiple possible field names
    avail_raw = str(
        event.get("availability", event.get("ticket_status", event.get("status", "")))
    ).lower()

    if "sold" in avail_raw or avail_raw == "0":
        availability = "Sold Out"
    elif "available" in avail_raw or avail_raw in ("1", "true", "open", "active"):
        availability = "Available"
    elif "fast" in avail_raw or "filling" in avail_raw:
        availability = "Filling Fast"
    elif avail_raw in ("", "none", "null"):
        # If the event is listed at all, assume available unless stated otherwise
        availability = "Available"
    else:
        availability = avail_raw.capitalize()

    # Build the deep-link booking URL if possible
    slug = event.get("slug", event.get("event_slug", ""))
    if slug:
        booking_url = f"https://shop.royalchallengers.com/ticket/{slug}"
    elif event_id and event_id != "unknown":
        booking_url = f"https://shop.royalchallengers.com/ticket?event={event_id}"
    else:
        booking_url = RCB_SHOP_URL

    return RCBMatch(
        event_id=event_id,
        name=name,
        venue=venue,
        match_date=raw_date,
        match_date_parsed=parsed_date,
        category=category,
        availability=availability,
        booking_url=booking_url,
        raw=event,
    )


def _try_parse_date(date_str: str) -> Optional[datetime]:
    """Tries several common date formats used by ticketing APIs."""
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%B %d, %Y",
        "%d %B %Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except (ValueError, AttributeError):
            continue
    return None


def get_april24_match() -> Optional[RCBMatch]:
    """
    Specifically looks for the April 24, 2025 RCB match.
    Returns None if not found (not yet listed or API is empty).
    """
    events = fetch_rcb_events()
    for event in events:
        if _is_april24(event):
            return event
    return None


def _is_april24(match: RCBMatch) -> bool:
    """Returns True if this match is on April 24."""
    if match.match_date_parsed:
        return (
            match.match_date_parsed.month == 4 and
            match.match_date_parsed.day == 24
        )
    # Fallback: string search
    date_str = match.match_date.lower()
    return "24" in date_str and ("apr" in date_str or "04" in date_str)


def check_rcb_availability() -> list[RCBMatch]:
    """Returns only matches with tickets currently available."""
    return [m for m in fetch_rcb_events() if m.availability in ("Available", "Filling Fast")]


def is_rcb_api_live() -> bool:
    """Quick health check — returns True if the API is reachable and returning data."""
    try:
        r = requests.get(RCB_API_URL, headers=RCB_HEADERS, timeout=10)
        data = r.json()
        return data.get("status") == "Success"
    except Exception:
        return False
