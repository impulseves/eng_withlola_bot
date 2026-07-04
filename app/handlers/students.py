from datetime import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.database import get_session
from app.repositories.students import approve_student, get_active_students, get_new_students
from config import is_admin


router = Router()


class ApproveStudent(StatesGroup):
    waiting_for_amount = State()
    waiting_for_payment_date = State()
    waiting_for_notes = State()


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

    if active_students:
        text += "Активные ученики:\n"
        for student in active_students:
            text += f"• {student.name} — {student.amount} ₽\n"

    await message.answer(text)


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
    await message.answer("Введите заметку по ученику или напишите '-' если заметка не нужна.")
    await state.set_state(ApproveStudent.waiting_for_notes)


@router.message(ApproveStudent.waiting_for_notes)
async def approve_student_notes(message: Message, state: FSMContext):
    data = await state.get_data()
    notes = None if message.text == "-" else message.text

    with get_session() as session:
        student = approve_student(
            session=session,
            student_id=data["student_id"],
            amount=data["amount"],
            payment_date=data["payment_date"],
            notes=notes,
        )

    await state.clear()

    if not student:
        await message.answer("Ученик с таким ID не найден.")
        return

    await message.answer(
        "✅ Ученик подтвержден.\n\n"
        f"Имя: {student.name}\n"
        f"Стоимость: {student.amount} ₽\n"
        f"Дата оплаты: {student.payment_date.strftime('%d.%m.%Y')}"
    )

