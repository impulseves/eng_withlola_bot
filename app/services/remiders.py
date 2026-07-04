from datetime import date

from aiogram import Bot

from app.database import get_session
from app.handlers.student import payment_button
from app.repositories.students import get_active_students


async def send_payment_reminders(bot: Bot) -> None:
    today = date.today()

    with get_session() as session:
        students = get_active_students(session)

    for student in students:
        if not student.payment_date:
            continue

        days_left = (student.payment_date - today).days

        if days_left == 5:
            text = (
                f"Здравствуйте, {student.name}!\n\n"
                "Напоминаем, что через 5 дней необходимо оплатить занятия.\n\n"
                f"Дата оплаты: {student.payment_date.strftime('%d.%m.%Y')}\n"
                f"Сумма: {student.amount} ₽"
            )

        elif days_left == 1:
            text = (
                f"Здравствуйте, {student.name}!\n\n"
                "Напоминаем, что завтра необходимо оплатить занятия.\n\n"
                f"Дата оплаты: {student.payment_date.strftime('%d.%m.%Y')}\n"
                f"Сумма: {student.amount} ₽"
            )

        else:
            continue

        await bot.send_message(
            chat_id=student.telegram_id,
            text=text,
            reply_markup=payment_button(),
        )
