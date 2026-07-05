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
                f"<b>Hey there!</b>\n\n"
                "У вас прошёл последний урок по абонементу.\n\n"
                "Пожалуйста, внесите оплату не позднее чем за 24 часа до следующего занятия ❤️\n\n"
                "Ссылка на оплату закреплена в чате. По возможности выбирайте оплату <b>через СБП</b>.\n\n"
                "После оплаты отправьте чек или скриншот в личные сообщения преподавателю "
                "и нажмите кнопку <b>«✅ Оплачено»</b> в боте."
            )

        elif days_left == 1:
            text = (
                f"<b>Hey there!</b>\n\n"
                "Завтра у вас запланирован урок. Пожалуйста, оплатите абонемент ❤️\n\n"
                "Ссылка на оплату закреплена в чате. По возможности выбирайте оплату <b>через СБП</b>.\n\n"
                "После оплаты отправьте чек или скриншот в личные сообщения преподавателю "
                "и нажмите кнопку <b>«✅ Оплачено»</b> в боте."
            )
        else:
            continue

        await bot.send_message(
            chat_id=student.telegram_id,
            text=text,
            reply_markup=payment_button(),
            parse_mode ="HTML",
        )
