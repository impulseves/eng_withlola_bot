from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def admin_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👥 Ученики"),
                KeyboardButton(text="➕ Новые ученики"),
            ],
            [
                KeyboardButton(text="📢 Рассылка"),
                KeyboardButton(text="📊 Статистика"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие",
    )

def student_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="💳 Моя оплата"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие",
    )
