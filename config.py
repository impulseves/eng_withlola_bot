import os
from dotenv import load_dotenv

load_dotenv()


BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS_RAW = os.getenv("ADMIN_IDS")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/students.db")

TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")
REMINDER_HOUR = int(os.getenv("REMINDER_HOUR", 9))
REMINDER_MINUTE = int(os.getenv("REMINDER_MINUTE", 0))


if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не указан в .env")

if not ADMIN_IDS_RAW:
    raise ValueError("ADMIN_IDS не указан в .env")


ADMIN_IDS = {
    int(x)
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x
}


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS