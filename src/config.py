import os
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Config:
    # Telegram
    telegram_bot_token: str
    telegram_chat_id: str

    # Scraping
    city: str = "bangalore"
    check_interval_seconds: int = 120   # Check every 2 minutes
    heartbeat_every_n_checks: int = 30  # Send a heartbeat every 30 checks (~1 hour)

    # Deduplication — don't re-alert for same match within this many seconds
    alert_cooldown_seconds: int = 3600  # 1 hour

    # Logging
    log_level: str = "INFO"


def load_config() -> Config:
    """Loads config from environment variables. Raises if required vars are missing."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    if not token:
        raise EnvironmentError(
            "TELEGRAM_BOT_TOKEN is not set. "
            "Create a bot via @BotFather on Telegram and set this env var."
        )
    if not chat_id:
        raise EnvironmentError(
            "TELEGRAM_CHAT_ID is not set. "
            "Get your chat ID by messaging @userinfobot on Telegram."
        )

    city = os.environ.get("CITY", "bangalore").strip().lower()
    check_interval = int(os.environ.get("CHECK_INTERVAL_SECONDS", "120"))
    heartbeat_every = int(os.environ.get("HEARTBEAT_EVERY_N_CHECKS", "30"))
    cooldown = int(os.environ.get("ALERT_COOLDOWN_SECONDS", "3600"))
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()

    config = Config(
        telegram_bot_token=token,
        telegram_chat_id=chat_id,
        city=city,
        check_interval_seconds=check_interval,
        heartbeat_every_n_checks=heartbeat_every,
        alert_cooldown_seconds=cooldown,
        log_level=log_level,
    )

    logger.info(f"Config loaded — City: {config.city}, Interval: {config.check_interval_seconds}s")
    return config
