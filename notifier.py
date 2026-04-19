import requests

import config
from logger import log


def send(msg):
    if not config.TELEGRAM_TOKEN or not config.CHAT_ID:
        log("Telegram notification skipped: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not configured")
        return False

    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": config.CHAT_ID, "text": msg}, timeout=10)
        return True
    except Exception as exc:
        log(f"Telegram notification failed: {exc}")
        return False
