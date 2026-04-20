"""
IPL Ticket Availability Alert Bot
----------------------------------
PRIMARY SOURCE : RCB TicketGenie API  → shop.royalchallengers.com/ticket
FALLBACK SOURCE: BookMyShow API       → bookmyshow.com

Priority watch: April 24 RCB home match.
Sends Telegram alerts the instant tickets go live.
Deploy on Railway/Render to run 24/7 without your laptop.
"""

import time
import logging
import sys
import importlib
from pathlib import Path

# Railway/Nixpacks can execute from varying working directories.
# Ensure both project root and src folder are importable.
BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
for p in (BASE_DIR, SRC_DIR):
    p_str = str(p)
    if p_str not in sys.path:
        sys.path.insert(0, p_str)

try:
    from src.config import load_config
    from src.rcb_scraper import (
        fetch_rcb_events,
        check_rcb_availability,
        get_april24_match,
        is_rcb_api_live,
    )
    from src.scraper import check_ticket_availability, get_all_matches
    from src.telegram_bot import (
        send_message,
        send_startup_message,
        send_heartbeat,
        format_match_alert,
        format_status_summary,
        format_rcb_alert,
        format_april24_watching,
        format_rcb_no_events,
    )
except ModuleNotFoundError:
    config_module = importlib.import_module("config")
    rcb_module = importlib.import_module("rcb_scraper")
    scraper_module = importlib.import_module("scraper")
    telegram_module = importlib.import_module("telegram_bot")

    load_config = config_module.load_config
    fetch_rcb_events = rcb_module.fetch_rcb_events
    check_rcb_availability = rcb_module.check_rcb_availability
    get_april24_match = rcb_module.get_april24_match
    is_rcb_api_live = rcb_module.is_rcb_api_live
    check_ticket_availability = scraper_module.check_ticket_availability
    get_all_matches = scraper_module.get_all_matches
    send_message = telegram_module.send_message
    send_startup_message = telegram_module.send_startup_message
    send_heartbeat = telegram_module.send_heartbeat
    format_match_alert = telegram_module.format_match_alert
    format_status_summary = telegram_module.format_status_summary
    format_rcb_alert = telegram_module.format_rcb_alert
    format_april24_watching = telegram_module.format_april24_watching
    format_rcb_no_events = telegram_module.format_rcb_no_events


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def run():
    # ── Config ───────────────────────────────────────────────────────────────
    try:
        config = load_config()
    except EnvironmentError as e:
        print(f"[FATAL] {e}")
        sys.exit(1)

    setup_logging(config.log_level)
    logger = logging.getLogger("main")

    logger.info("=" * 60)
    logger.info("  IPL Ticket Alert Bot")
    logger.info("  Primary  : RCB TicketGenie (shop.royalchallengers.com)")
    logger.info("  Fallback : BookMyShow")
    logger.info(f"  City     : {config.city}")
    logger.info(f"  Interval : {config.check_interval_seconds}s")
    logger.info("  Priority : April 24 RCB match 🔴")
    logger.info("=" * 60)

    # ── Startup Telegram message ─────────────────────────────────────────────
    send_startup_message(
        config.telegram_bot_token,
        config.telegram_chat_id,
        config.city,
        config.check_interval_seconds,
    )

    # ── Check RCB API health on startup ─────────────────────────────────────
    rcb_live = is_rcb_api_live()
    if rcb_live:
        logger.info("[RCB] API is reachable ✅")
        rcb_events = fetch_rcb_events()
        if rcb_events:
            # Send a summary of what's listed
            lines = ["🔴 <b>RCB TicketGenie — Current Listings</b>\n"]
            for e in rcb_events:
                emoji = "🟢" if e.availability == "Available" else ("🟡" if "fast" in e.availability.lower() else "🔴")
                lines.append(f"{emoji} {e.name}\n   📅 {e.match_date} | {e.availability}\n   <a href='{e.booking_url}'>→ Book</a>\n")
            send_message(config.telegram_bot_token, config.telegram_chat_id, "\n".join(lines))
        else:
            send_message(config.telegram_bot_token, config.telegram_chat_id, format_rcb_no_events())

        # Specific April 24 watch notice
        apr24 = get_april24_match()
        if apr24:
            send_message(
                config.telegram_bot_token,
                config.telegram_chat_id,
                format_rcb_alert(apr24, is_priority=True),
            )
        else:
            send_message(
                config.telegram_bot_token,
                config.telegram_chat_id,
                format_april24_watching(),
            )
    else:
        logger.warning("[RCB] API not reachable on startup — will use BMS fallback")
        send_message(
            config.telegram_bot_token,
            config.telegram_chat_id,
            "⚠️ RCB TicketGenie API is unreachable right now. Falling back to BookMyShow monitoring.",
        )

    # ── BMS fallback startup summary ─────────────────────────────────────────
    bms_matches = get_all_matches(config.city)
    if bms_matches:
        send_message(
            config.telegram_bot_token,
            config.telegram_chat_id,
            format_status_summary(bms_matches, config.city),
        )

    # ── Deduplication cache ───────────────────────────────────────────────────
    alerted_events: dict = {}    # event_id/code -> last alerted timestamp (float)
    april24_alerted = False       # special flag for April 24 match
    checks_done = 0

    # ── Main loop ─────────────────────────────────────────────────────────────
    while True:
        try:
            checks_done += 1
            logger.info(f"── Check #{checks_done} ─────────────────────────────────")
            now = time.time()

            # ── 1. RCB TicketGenie (PRIMARY) ──────────────────────────────────
            rcb_available = check_rcb_availability()

            if rcb_available:
                for match in rcb_available:
                    last = alerted_events.get(f"rcb_{match.event_id}", 0)
                    if (now - last) > config.alert_cooldown_seconds:
                        is_apr24 = (
                            match.match_date_parsed and
                            match.match_date_parsed.month == 4 and
                            match.match_date_parsed.day == 24
                        )
                        logger.info(f"[RCB] ALERT: {match.name} | {match.availability} | Apr24={is_apr24}")
                        text = format_rcb_alert(match, is_priority=is_apr24)
                        ok = send_message(config.telegram_bot_token, config.telegram_chat_id, text)
                        if ok:
                            alerted_events[f"rcb_{match.event_id}"] = now
                            if is_apr24:
                                april24_alerted = True
            else:
                logger.info("[RCB] No available tickets from TicketGenie right now")

                # If April 24 match exists but is Sold Out, alert once
                apr24 = get_april24_match()
                if apr24:
                    key = f"rcb_{apr24.event_id}_status_{apr24.availability}"
                    if key not in alerted_events:
                        send_message(
                            config.telegram_bot_token,
                            config.telegram_chat_id,
                            f"📋 <b>April 24 match status update</b>\n\n"
                            f"Match: {apr24.name}\n"
                            f"Status: <b>{apr24.availability}</b>\n"
                            f"🔗 <a href='{apr24.booking_url}'>Check on RCB site</a>",
                        )
                        alerted_events[key] = now

            # ── 2. BookMyShow fallback ────────────────────────────────────────
            bms_available = check_ticket_availability(config.city)
            for match in bms_available:
                key = f"bms_{match.event_code}"
                last = alerted_events.get(key, 0)
                if (now - last) > config.alert_cooldown_seconds:
                    logger.info(f"[BMS] ALERT: {match.name} | {match.availability}")
                    text = format_match_alert(match)
                    ok = send_message(config.telegram_bot_token, config.telegram_chat_id, text)
                    if ok:
                        alerted_events[key] = now

            # ── 3. Heartbeat every N checks ───────────────────────────────────
            if checks_done % config.heartbeat_every_n_checks == 0:
                send_heartbeat(
                    config.telegram_bot_token,
                    config.telegram_chat_id,
                    config.city,
                    checks_done,
                )

        except KeyboardInterrupt:
            logger.info("Bot stopped.")
            send_message(
                config.telegram_bot_token,
                config.telegram_chat_id,
                "🛑 <b>IPL Alert Bot stopped.</b> Restart the Railway/Render service to resume.",
            )
            break

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            time.sleep(30)
            continue

        time.sleep(config.check_interval_seconds)


if __name__ == "__main__":
    run()
