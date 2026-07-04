import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.database import get_session, init_db
from app.repositories.students import get_or_create_student
from config import BOT_TOKEN, is_admin

from app.keyboards import admin_main_menu
from app.handlers import routers
from app.scheduler import scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start_handler(message: Message):
    user = message.from_user

    if is_admin(user.id):
        await message.answer(
            "Здравствуйте! Вы вошли как преподаватель.\n\n"
            "Выберите действие в меню ниже.",
            reply_markup = admin_main_menu(),
        )
        return

    with get_session() as session:
        student, created = get_or_create_student(
            session=session,
            telegram_id=user.id,
            name=user.full_name,
            username=user.username,
        )

    if created:
        await message.answer(
            "Здравствуйте!\n\n"
            "Вы зарегистрировались в боте.\n"
            "После подтверждения преподавателем вы будете получать уведомления об оплате."
        )
    else:
        await message.answer(
            "Здравствуйте!\n\n"
            "Вы уже зарегистрированы в боте.\n"
            "Если преподаватель вас активировал, скоро здесь появится информация об оплате."
        )


async def main():
    init_db()
    setup_scheduler(bot)
    for router in routers:
        dp.include_router(router)
    logging.info("Бот запускается...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
