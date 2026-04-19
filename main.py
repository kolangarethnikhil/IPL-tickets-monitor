"""
IPL Ticket Availability Alert Bot
----------------------------------
Monitors BookMyShow for IPL ticket availability and sends
instant Telegram alerts when tickets open up.

Deploy on Railway / Render to run 24/7 without your laptop.
"""

import time
import logging
import sys

from src.config import load_config
from src.scraper import check_ticket_availability, get_all_matches
from src.telegram_bot import (
    send_message,
    send_startup_message,
    send_heartbeat,
    format_match_alert,
    format_status_summary,
)


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def run():
    # ── Load config ──────────────────────────────────────────────────────────
    try:
        config = load_config()
    except EnvironmentError as e:
        print(f"[FATAL] {e}")
        sys.exit(1)

    setup_logging(config.log_level)
    logger = logging.getLogger("main")

    logger.info("=" * 60)
    logger.info("  IPL Ticket Alert Bot — Starting Up")
    logger.info(f"  City     : {config.city}")
    logger.info(f"  Interval : {config.check_interval_seconds}s")
    logger.info("=" * 60)

    # ── Send startup message ─────────────────────────────────────────────────
    send_startup_message(
        config.telegram_bot_token,
        config.telegram_chat_id,
        config.city,
        config.check_interval_seconds,
    )

    # ── Send initial status summary ──────────────────────────────────────────
    all_matches = get_all_matches(config.city)
    summary = format_status_summary(all_matches, config.city)
    send_message(config.telegram_bot_token, config.telegram_chat_id, summary)

    # ── Alert deduplication — track which events we've already alerted ───────
    alerted_events: dict = {}  # event_code -> last alerted timestamp

    checks_done = 0

    # ── Main loop ─────────────────────────────────────────────────────────────
    while True:
        try:
            logger.info(f"Check #{checks_done + 1} — scanning for available IPL tickets in {config.city}...")

            available_matches = check_ticket_availability(config.city)
            now = time.time()

            for match in available_matches:
                last_alerted = alerted_events.get(match.event_code, 0)
                cooldown_expired = (now - last_alerted) > config.alert_cooldown_seconds

                if cooldown_expired:
                    logger.info(f"ALERT: {match.name} — {match.availability}")
                    alert_text = format_match_alert(match)
                    success = send_message(
                        config.telegram_bot_token,
                        config.telegram_chat_id,
                        alert_text,
                    )
                    if success:
                        alerted_events[match.event_code] = now
                else:
                    logger.debug(f"Skipping {match.event_code} — already alerted recently")

            if not available_matches:
                logger.info("No available tickets found yet. Will check again shortly.")

            checks_done += 1

            # ── Heartbeat every N checks ─────────────────────────────────────
            if checks_done % config.heartbeat_every_n_checks == 0:
                send_heartbeat(
                    config.telegram_bot_token,
                    config.telegram_chat_id,
                    config.city,
                    checks_done,
                )

        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")
            send_message(
                config.telegram_bot_token,
                config.telegram_chat_id,
                "Bot stopped. Restart the service to resume monitoring.",
            )
            break

        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
            time.sleep(30)
            continue

        time.sleep(config.check_interval_seconds)


if __name__ == "__main__":
    run()
