from datetime import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.database import get_session
from app.repositories.students import approve_student, get_active_students, get_new_students, reject_payment, get_student_payments, get_by_id
from config import is_admin
from app.keyboards import student_main_menu

from app.repositories.students import (
    approve_student,
    confirm_payment,
    deactivate_student,
    get_active_students,
    get_by_id,
    get_new_students,
    get_pending_payments,
    get_student_payments,
    reject_payment,
    update_student_amount,
    update_student_payment_date,
    update_student_period,
)


router = Router()


class ApproveStudent(StatesGroup):
    waiting_for_amount = State()
    waiting_for_payment_date = State()
    waiting_for_period = State()

class EditStudent(StatesGroup):
    waiting_for_amount = State()
    waiting_for_payment_date = State()
    waiting_for_period = State()

@router.message(F.text == "👥 Ученики")
async def students_menu(message: Message):
    if not is_admin(message.from_user.id):
        return

    with get_session() as session:
        active_students = get_active_students(session)
        new_students = get_new_students(session)

    text = "👥 Ученики\n\n"
    text += f"🟢 Активные: {len(active_students)}\n"
    text += f"🆕 Новые: {len(new_students)}\n\n"

    await message.answer(text)

    for student in active_students:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="👤 Открыть карточку",
                        callback_data=f"student_card:{student.id}",
                    )
                ]
            ]
        )

        await message.answer(
            f"👤 {student.name}\n"
            f"💰 {student.amount} ₽\n"
            f"📅 {student.payment_date.strftime('%d.%m.%Y') if student.payment_date else 'не указана'}",
            reply_markup=keyboard,
        )



@router.message(F.text == "➕ Новые ученики")
async def new_students_menu(message: Message):
    if not is_admin(message.from_user.id):
        return

    with get_session() as session:
        new_students = get_new_students(session)

    if not new_students:
        await message.answer("Новых учеников пока нет.")
        return

    for student in new_students:
        username = f"@{student.username}" if student.username else "без username"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Подтвердить",
                        callback_data=f"approve_student:{student.id}",
                    )
                ]
            ]
        )

        await message.answer(
            f"🆕 Новый ученик\n\n"
            f"ID: {student.id}\n"
            f"Имя: {student.name}\n"
            f"Telegram: {username}",
            reply_markup=keyboard,
        )


@router.callback_query(F.data.startswith("approve_student:"))
async def approve_student_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    student_id = int(callback.data.split(":")[1])
    await state.update_data(student_id=student_id)

    await callback.message.answer("Введите стоимость занятий в рублях, например: 3000")
    await state.set_state(ApproveStudent.waiting_for_amount)

    await callback.answer()


@router.message(ApproveStudent.waiting_for_amount)
async def approve_student_amount(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите сумму числом, например: 3000")
        return

    await state.update_data(amount=int(message.text))
    await message.answer("Введите дату ближайшей оплаты в формате ДД.ММ.ГГГГ, например: 15.09.2026")
    await state.set_state(ApproveStudent.waiting_for_payment_date)


@router.message(ApproveStudent.waiting_for_payment_date)
async def approve_student_payment_date(message: Message, state: FSMContext):
    try:
        payment_date = datetime.strptime(message.text, "%d.%m.%Y").date()
    except ValueError:
        await message.answer("Неверный формат даты. Введите так: 15.09.2026")
        return

    await state.update_data(payment_date=payment_date)

    await message.answer(
        "Введите период оплаты в неделях.\n\n"
    )
    await state.set_state(ApproveStudent.waiting_for_period)

@router.message(ApproveStudent.waiting_for_period)
async def approve_student_period(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer(
            "Введите количество недель числом.\n\n"
            "Например: 4"
        )
        return
        
    period_weeks = int(message.text)

    if period_weeks <= 0:
        await message.answer("Период должен быть больше нуля.")
        return

    data = await state.get_data()

    with get_session() as session:
        student = approve_student(
            session=session,
            student_id=data["student_id"],
            amount=data["amount"],
            payment_date=data["payment_date"],
            period_weeks=period_weeks,
        )

    await state.clear()

    if not student:
        await message.answer("Ученик с таким ID не найден.")
        return

    await message.answer(
        "✅ Ученик подтвержден.\n\n"
        f"Имя: {student.name}\n"
        f"Стоимость: {student.amount} ₽\n"
        f"Дата оплаты: {student.payment_date.strftime('%d.%m.%Y')}\n"
        f"Период: {student.period_weeks} нед."
    )

    await message.bot.send_message(
        chat_id=student.telegram_id,
        text=(
            "✅ Преподаватель подтвердил вас.\n\n"
            "Теперь вы можете смотреть информацию об оплате.\n"
            "Для этого нажмите кнопку «💳 Моя оплата»."
        ),
        reply_markup=student_main_menu(),
    )

@router.callback_query(F.data.startswith("confirm_payment:"))
async def confirm_payment_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    student_id = int(callback.data.split(":")[1])

    with get_session() as session:
        student = confirm_payment(session, student_id)

    if not student:
        await callback.message.edit_text("Не удалось подтвердить оплату.")
        await callback.answer()
        return

    await callback.message.edit_text(
        "✅ Оплата подтверждена.\n\n"
        f"Ученик: {student.name}\n"
        f"Следующая дата оплаты: {student.payment_date.strftime('%d.%m.%Y')}"
    )

    await callback.answer()

@router.message(F.text == "💳 Оплаты")
async def payments_menu(message: Message):
    if not is_admin(message.from_user.id):
        return

    with get_session() as session:
        pending_students = get_pending_payments(session)

    if not pending_students:
        await message.answer("💳 Оплаты\n\nОжидающих подтверждения оплат нет.")
        return

    text = "💳 Ожидают подтверждения оплаты:\n\n"

    for student in pending_students:
        payment_date = (
            student.payment_date.strftime("%d.%m.%Y")
            if student.payment_date
            else "не указана"
        )

        text += (
            f"• {student.name}\n"
            f"  Сумма: {student.amount} ₽\n"
            f"  Дата оплаты: {payment_date}\n\n"
        )

    await message.answer(text)


@router.callback_query(F.data.startswith("reject_payment:"))
async def reject_payment_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    student_id = int(callback.data.split(":")[1])

    with get_session() as session:
        student = reject_payment(session, student_id)

    if not student:
        await callback.message.answer("Не удалось отклонить оплату.")
        await callback.answer()
        return

    await callback.bot.send_message(
        chat_id=student.telegram_id,
        text=(
            "❌ Оплата не подтверждена.\n\n"
            "Пожалуйста, проверьте перевод. "
            "Если оплата прошла, нажмите «✅ Оплачено» повторно."
        ),
    )

    await callback.message.edit_text(
        "❌ Оплата отклонена.\n\n"
        f"Ученик: {student.name}\n"
        "Дата оплаты не изменилась"
    )
    await callback.answer()

@router.message(F.text == "📜 История оплат")
async def payment_history_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await message.answer("Введите ID ученика:")
    await state.set_state(PaymentHistory.waiting_for_student_id)


class PaymentHistory(StatesGroup):
    waiting_for_student_id = State()


@router.message(PaymentHistory.waiting_for_student_id)
async def payment_history_show(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите числовой ID ученика.")
        return

    student_id = int(message.text)

    with get_session() as session:
        payments = get_student_payments(session, student_id)

    await state.clear()

    if not payments:
        await message.answer("История оплат по этому ученику пока пустая.")
        return

    text = "📜 История оплат\n\n"

    for payment in payments:
        text += (
            f"• {payment.due_date.strftime('%d.%m.%Y')}\n"
            f"  Сумма: {payment.amount} ₽\n"
            f"  Подтверждено: {payment.confirmed_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        )

    await message.answer(text)

async def send_student_card(message: Message, student_id: int):
    with get_session() as session:
        student = get_by_id(session, student_id)
        payments = get_student_payments(session, student_id)

    if not student:
        await message.answer("Ученик не найден.")
        return

    last_payment = (
        student.last_payment_date.strftime("%d.%m.%Y")
        if student.last_payment_date
        else "нет"
    )

    payment_date = (
        student.payment_date.strftime("%d.%m.%Y")
        if student.payment_date
        else "не указана"
    )

    total_paid = sum(payment.amount for payment in payments)

    text = (
        f"👤 {student.name}\n\n"
        f"Telegram: @{student.username if student.username else 'без username'}\n"
        f"💰 Стоимость: {student.amount} ₽\n"
        f"🔁 Период: {student.period_weeks} нед.\n"
        f"📅 Следующая оплата: {payment_date}\n"
        f"📈 Всего оплачено: {total_paid} ₽\n"
        f"💳 Количество оплат: {len(payments)}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Изменить",
                    callback_data=f"edit_student:{student.id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📜 История оплат",
                    callback_data=f"payment_history:{student.id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⛔ Отключить ученика",
                    callback_data=f"deactivate_student:{student.id}",
                )
            ],
        ]
    )

    await message.answer(text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("student_card:"))
async def student_card_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    student_id = int(callback.data.split(":")[1])

    await send_student_card(callback.message, student_id)
    await callback.answer()

@router.callback_query(F.data.startswith("payment_history:"))
async def payment_history_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    student_id = int(callback.data.split(":")[1])

    with get_session() as session:
        student = get_by_id(session, student_id)
        payments = get_student_payments(session, student_id)

    if not student:
        await callback.message.answer("Ученик не найден.")
        await callback.answer()
        return

    if not payments:
        await callback.message.answer(
            f"📜 История оплат\n\n"
            f"Ученик: {student.name}\n\n"
            "История оплат пока пустая."
        )
        await callback.answer()
        return

    text = f"📜 История оплат\n\nУченик: {student.name}\n\n"

    for payment in payments:
        text += (
            f"• {payment.due_date.strftime('%d.%m.%Y')}\n"
            f"  Сумма: {payment.amount} ₽\n"
            f"  Подтверждено: {payment.confirmed_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        )

    await callback.message.answer(text)
    await callback.answer()

@router.callback_query(F.data.startswith("deactivate_student:"))
async def deactivate_student_confirm(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    student_id = int(callback.data.split(":")[1])

    with get_session() as session:
        student = get_by_id(session, student_id)

    if not student:
        await callback.message.answer("Ученик не найден.")
        await callback.answer()
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, отключить",
                    callback_data=f"deactivate_student_confirm:{student.id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="↩️ Отмена",
                    callback_data=f"student_card:{student.id}",
                )
            ],
        ]
    )

    await callback.message.edit_text(
        "⚠️ Вы действительно хотите отключить ученика?\n\n"
        f"👤 {student.name}\n\n"
        "После отключения:\n"
        "• напоминания перестанут приходить;\n"
        "• ученик не будет получать рассылки;\n"
        "• история оплат сохранится.",
        reply_markup=keyboard,
    )

    await callback.answer()

@router.callback_query(F.data.startswith("deactivate_student_confirm:"))
async def deactivate_student_finish(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    student_id = int(callback.data.split(":")[1])

    with get_session() as session:
        student = deactivate_student(session, student_id)

    if not student:
        await callback.message.answer("Ученик не найден.")
        await callback.answer()
        return

    await callback.message.edit_text(
        "⛔ Ученик отключен.\n\n"
        f"👤 {student.name}\n\n"
        "Он больше не будет получать напоминания и рассылки.\n"
        "История оплат сохранена."
    )

    await callback.answer()
@router.callback_query(F.data.startswith("edit_student:"))
async def edit_student_menu(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    student_id = int(callback.data.split(":")[1])

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💰 Изменить сумму",
                    callback_data=f"edit_amount:{student_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📅 Изменить дату оплаты",
                    callback_data=f"edit_payment_date:{student_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔁 Изменить период",
                    callback_data=f"edit_period:{student_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="↩️ Назад к карточке",
                    callback_data=f"student_card:{student_id}",
                )
            ],
        ]
    )

    await callback.message.edit_text(
        "✏️ Что изменить?",
        reply_markup=keyboard,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_amount:"))
async def edit_amount_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    student_id = int(callback.data.split(":")[1])
    await state.update_data(student_id=student_id)

    await callback.message.answer("Введите новую сумму в рублях, например: 3000")
    await state.set_state(EditStudent.waiting_for_amount)
    await callback.answer()


@router.message(EditStudent.waiting_for_amount)
async def edit_amount_finish(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите сумму числом, например: 3000")
        return

    data = await state.get_data()

    with get_session() as session:
        student = update_student_amount(
            session=session,
            student_id=data["student_id"],
            amount=int(message.text),
        )

    await state.clear()

    if not student:
        await message.answer("Ученик не найден.")
        return

    await message.answer("✅ Сумма обновлена.")
    await send_student_card(message, student.id)



@router.callback_query(F.data.startswith("edit_payment_date:"))
async def edit_payment_date_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    student_id = int(callback.data.split(":")[1])
    await state.update_data(student_id=student_id)

    await callback.message.answer("Введите новую дату оплаты в формате ДД.ММ.ГГГГ, например: 15.09.2026")
    await state.set_state(EditStudent.waiting_for_payment_date)
    await callback.answer()


@router.message(EditStudent.waiting_for_payment_date)
async def edit_payment_date_finish(message: Message, state: FSMContext):
    try:
        payment_date = datetime.strptime(message.text, "%d.%m.%Y").date()
    except ValueError:
        await message.answer("Неверный формат даты. Введите так: 15.09.2026")
        return

    data = await state.get_data()

    with get_session() as session:
        student = update_student_payment_date(
            session=session,
            student_id=data["student_id"],
            payment_date=payment_date,
        )

    await state.clear()

    if not student:
        await message.answer("Ученик не найден.")
        return

    await message.answer("✅ Дата оплаты обновлена.")
    await send_student_card(message, student.id)



@router.callback_query(F.data.startswith("edit_period:"))
async def edit_period_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    student_id = int(callback.data.split(":")[1])
    await state.update_data(student_id=student_id)

    await callback.message.answer("Введите новый период оплаты в неделях, например: 4")
    await state.set_state(EditStudent.waiting_for_period)
    await callback.answer()


@router.message(EditStudent.waiting_for_period)
async def edit_period_finish(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите количество недель числом, например: 4")
        return

    period_weeks = int(message.text)

    if period_weeks <= 0:
        await message.answer("Период должен быть больше нуля.")
        return

    data = await state.get_data()

    with get_session() as session:
        student = update_student_period(
            session=session,
            student_id=data["student_id"],
            period_weeks=period_weeks,
        )

    await state.clear()

    if not student:
        await message.answer("Ученик не найден.")
        return

    await message.answer("✅ Период обновлен.")
    await send_student_card(message, student.id)

