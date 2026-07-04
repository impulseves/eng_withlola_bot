from aiogram import Router, F
from aiogram.types import Message

from config import is_admin


router = Router()


@router.message(F.text == "📊 Статистика")
async def stats_menu(message: Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer("📊 Статистика скоро будет здесь.")
