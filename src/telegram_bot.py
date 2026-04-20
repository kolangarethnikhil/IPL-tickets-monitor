import requests
import logging

try:
    from src.scraper import MatchInfo
    from src.rcb_scraper import RCBMatch
except ModuleNotFoundError:
    from scraper import MatchInfo
    from rcb_scraper import RCBMatch

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


def send_message(bot_token: str, chat_id: str, text: str, parse_mode: str = "HTML") -> bool:
    """Sends a message via Telegram Bot API."""
    url = TELEGRAM_API.format(token=bot_token, method="sendMessage")
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": False,
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False


def format_match_alert(match: MatchInfo) -> str:
    """Formats a single match into a clean Telegram alert message."""
    status_emoji = "🟢" if match.availability == "Available" else "🟡"

    return (
        f"🏏 <b>IPL TICKETS ALERT!</b>\n\n"
        f"{status_emoji} <b>Status:</b> {match.availability}\n"
        f"📋 <b>Match:</b> {match.name}\n"
        f"🏟️ <b>Venue:</b> {match.venue}\n"
        f"📅 <b>Date:</b> {match.date}\n"
        f"📍 <b>City:</b> {match.city}\n\n"
        f"🎟️ <a href='{match.booking_url}'>Book Now on BookMyShow</a>\n\n"
        f"⚡ <i>Grab them before they're gone!</i>"
    )


def format_status_summary(matches: list[MatchInfo], city: str) -> str:
    """Formats a full status digest of all upcoming matches."""
    if not matches:
        return (
            f"🏏 <b>IPL Ticket Status — {city.capitalize()}</b>\n\n"
            f"😴 No upcoming IPL matches found on BookMyShow for {city.capitalize()} right now.\n"
            f"I'll keep checking every few minutes!"
        )

    lines = [f"🏏 <b>IPL Ticket Status — {city.capitalize()}</b>\n"]
    for m in matches:
        if m.availability == "Available":
            emoji = "🟢"
        elif m.availability == "Filling Fast":
            emoji = "🟡"
        elif m.availability == "Sold Out":
            emoji = "🔴"
        else:
            emoji = "⚪"

        lines.append(
            f"{emoji} <b>{m.name}</b>\n"
            f"   📅 {m.date} | 🏟️ {m.venue}\n"
            f"   Status: {m.availability}\n"
            f"   <a href='{m.booking_url}'>→ BookMyShow</a>\n"
        )

    lines.append("\n⏱️ <i>Auto-checking every few minutes. You'll be alerted the moment tickets open!</i>")
    return "\n".join(lines)


def send_startup_message(bot_token: str, chat_id: str, city: str, interval: int) -> bool:
    """Sends a confirmation message when the bot starts."""
    msg = (
        f"🚀 <b>IPL Ticket Alert Bot Started!</b>\n\n"
        f"📍 Watching tickets for: <b>{city.capitalize()}</b>\n"
        f"⏱️ Check interval: every <b>{interval} seconds</b>\n"
        f"📲 You'll get a message here the moment IPL tickets go live on BookMyShow!\n\n"
        f"🛑 To stop the bot, shut down your Railway/Render service."
    )
    return send_message(bot_token, chat_id, msg)


def send_heartbeat(bot_token: str, chat_id: str, city: str, checks_done: int) -> bool:
    """Periodic 'still alive' message so you know the bot is running."""
    msg = (
        f"💓 <b>Bot Heartbeat</b>\n\n"
        f"Still watching IPL tickets for <b>{city.capitalize()}</b>.\n"
        f"Total checks completed: <b>{checks_done}</b>\n"
        f"No available tickets yet — will alert you the moment they drop!"
    )
    return send_message(bot_token, chat_id, msg)


def format_rcb_alert(match, is_priority: bool = False) -> str:
    """Formats an RCB TicketGenie match into a Telegram alert."""
    status_emoji = "🟢" if match.availability == "Available" else "🟡"
    priority_banner = "🔥 <b>PRIORITY MATCH ALERT — APRIL 24!</b>\n\n" if is_priority else ""

    return (
        f"{priority_banner}"
        f"🏏 <b>RCB TICKETS ALERT!</b>\n\n"
        f"{status_emoji} <b>Status:</b> {match.availability}\n"
        f"📋 <b>Match:</b> {match.name}\n"
        f"🏟️ <b>Venue:</b> {match.venue}\n"
        f"📅 <b>Date:</b> {match.match_date}\n"
        f"🏷️ <b>Category:</b> {match.category}\n\n"
        f"🎟️ <a href='{match.booking_url}'>Book on RCB Official Site</a>\n"
        f"🔗 <a href='https://shop.royalchallengers.com/ticket'>All RCB Tickets</a>\n\n"
        f"⚡ <i>Grab them before they sell out — Ee Sala Cup Namde! 🔴🟡</i>"
    )


def format_april24_watching() -> str:
    return (
        "👀 <b>Watching April 24 RCB Match</b>\n\n"
        "Tickets for the <b>April 24 RCB home match</b> are not live yet.\n\n"
        "Checking the RCB TicketGenie API every few minutes — you'll get an alert "
        "<b>the instant they go live!</b> 🔴\n\n"
        "📌 Get ready:\n"
        "👉 https://shop.royalchallengers.com/ticket"
    )


def format_rcb_no_events() -> str:
    return (
        "⚪ <b>RCB API: No events listed yet</b>\n\n"
        "The RCB TicketGenie API returned 0 events right now.\n"
        "This usually means the sales window hasn't opened yet.\n\n"
        "Still watching — I'll alert you the moment anything appears! 🔴\n"
        "🔗 <a href='https://shop.royalchallengers.com/ticket'>Check manually</a>"
    )
