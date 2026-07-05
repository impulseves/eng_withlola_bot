from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.database import get_session
from app.repositories.students import get_by_telegram_id, set_payment_pending
from config import ADMIN_IDS


router = Router()

def payment_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Оплачено",
                    callback_data="student_paid",
                )
            ]
        ]
    )


@router.message(F.text == "💳 Моя оплата")
async def my_payment(message: Message):
    with get_session() as session:
        student = get_by_telegram_id(session, message.from_user.id)

    if not student:
        await message.answer("Вы пока не зарегистрированы. Нажмите /start.")
        return

    if not student.approved or not student.active:
        await message.answer(
            "Ваша регистрация еще не подтверждена преподавателем."
        )
        return

    await message.answer(
        "💳 Информация об оплате\n\n"
        f"Стоимость: {student.amount} ₽\n"
        f"Дата следующей оплаты: {student.payment_date.strftime('%d.%m.%Y')}",
        reply_markup=payment_button(),
    )

@router.callback_query(F.data == "student_paid")
async def student_paid_callback(callback: CallbackQuery):
    with get_session() as session:
        student = get_by_telegram_id(session, callback.from_user.id)

        if not student:
            await callback.message.answer("Вы пока не зарегистрированы. Нажмите /start.")
            await callback.answer()
            return

        if not student.approved or not student.active:
            await callback.message.answer("Ваша регистрация еще не подтверждена преподавателем.")
            await callback.answer()
            return

        set_payment_pending(session, student.id, True)

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Подтвердить",
                        callback_data=f"confirm_payment:{student.id}",
                    ),
                    InlineKeyboardButton(
                          text="❌ Оплата не прошла",
                         callback_data=f"reject_payment:{student.id}",
                    )
                ]
            ]
        )

        for admin_id in ADMIN_IDS:
            await callback.bot.send_message(
                admin_id,
                "🔔 Ученик сообщил об оплате.\n\n"
                f"Имя: {student.name}\n"
                f"Сумма: {student.amount} ₽\n"
                f"Дата оплаты: {student.payment_date.strftime('%d.%m.%Y')}",
                reply_markup=keyboard,
            )

    await callback.message.answer(
        "Спасибо!\n\n"
        "Сообщение об оплате отправлено преподавателю."
    )

    await callback.answer()
