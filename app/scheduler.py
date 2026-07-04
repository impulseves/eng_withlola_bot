from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.services.reminders import send_payment_reminders
from config import REMINDER_HOUR, REMINDER_MINUTE, TIMEZONE


def setup_scheduler(bot):
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)

    scheduler.add_job(
        send_payment_reminders,
        trigger="cron",
        hour=REMINDER_HOUR,
        minute=REMINDER_MINUTE,
        kwargs={"bot": bot},
    )

    scheduler.start()

    return scheduler
