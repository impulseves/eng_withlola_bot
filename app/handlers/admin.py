from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from app.database import get_session
from app.repositories.students import get_active_students
from config import is_admin


router = Router()


class Broadcast(StatesGroup):
    waiting_for_text = State()


@router.message(F.text == "📊 Статистика")
async def stats_menu(message: Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer("📊 Статистика скоро будет здесь.")


@router.message(F.text == "📢 Рассылка")
async def broadcast_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await message.answer("Введите текст рассылки:")
    await state.set_state(Broadcast.waiting_for_text)


@router.message(Broadcast.waiting_for_text)
async def broadcast_send(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    text = message.text

    with get_session() as session:
        students = get_active_students(session)

    success = 0
    failed = 0

    for student in students:
        try:
            await message.bot.send_message(
                chat_id=student.telegram_id,
                text=text,
            )
            success += 1
        except Exception:
            failed += 1

    await state.clear()

    await message.answer(
        "📢 Рассылка завершена.\n\n"
        f"Отправлено: {success}\n"
        f"Ошибок: {failed}"
    )
