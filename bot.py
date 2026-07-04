import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

from config import BOT_TOKEN, is_admin


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start_handler(message: Message):
    user_id = message.from_user.id

    if is_admin(user_id):
        await message.answer(
            "Здравствуйте! Вы вошли как преподаватель.\n\n"
            "Скоро здесь будет главное меню бота."
        )
    else:
        await message.answer(
            "Здравствуйте!\n\n"
            "Этот бот используется для уведомлений о занятиях и оплате.\n"
            "После активации преподавателем вы будете получать уведомления."
        )


async def main():
    logging.info("Бот запускается...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())