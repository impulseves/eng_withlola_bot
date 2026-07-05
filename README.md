# English with Lola Bot

Telegram-бот для преподавателя английского языка.

## Стек

- Python 3.14
- Aiogram 3
- SQLAlchemy
- SQLite
- APScheduler
- systemd (Linux)

---

## Структура проекта

```
eng_withlola_bot/
├── app/
├── data/
├── .venv/
├── .env
├── bot.py
├── config.py
├── requirements.txt
└── README.md
```

---

## Первый запуск

```bash
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

python bot.py
```

---

## Запуск через systemd

Запустить:

```bash
sudo systemctl start eng-withlola-bot
```

Остановить:

```bash
sudo systemctl stop eng-withlola-bot
```

Перезапустить:

```bash
sudo systemctl restart eng-withlola-bot
```

Проверить статус:

```bash
sudo systemctl status eng-withlola-bot
```

Просмотреть логи:

```bash
sudo journalctl -u eng-withlola-bot -f
```

Перезагрузить конфигурацию systemd после изменения service-файла:

```bash
sudo systemctl daemon-reload
```

---

## Git

Проверить изменения:

```bash
git status
```

Добавить изменения:

```bash
git add .
```

Создать коммит:

```bash
git commit -m "Описание изменений"
```

Отправить в GitHub:

```bash
git push
```

Получить изменения:

```bash
git pull
```

---

## Ручная проверка напоминаний

```bash
python -c "import asyncio; from aiogram import Bot; from config import BOT_TOKEN; from app.services.reminders import send_payment_reminders; asyncio.run(send_payment_reminders(Bot(BOT_TOKEN)))"
```

---

## База данных

Открыть SQLite:

```bash
sqlite3 data/students.db
```

Показать таблицы:

```sql
.tables
```

Показать учеников:

```sql
SELECT id, name, payment_date, period_weeks FROM students;
```

Выход:

```sql
.exit
```

---

## Настройки

Основные параметры находятся в `.env`:

```env
BOT_TOKEN=
ADMIN_IDS=
TIMEZONE=Europe/Moscow
REMINDER_HOUR=10
REMINDER_MINUTE=0
DATABASE_URL=sqlite:///data/students.db
```

---

## Основной функционал

### Для ученика

- Регистрация
- Просмотр оплаты
- Подтверждение оплаты
- Напоминания

### Для преподавателя

- Подтверждение ученика
- Редактирование суммы
- Редактирование даты оплаты
- Редактирование периода
- История оплат
- Статистика
- Рассылка
- Отключение ученика

---

## Резервное копирование

Создать резервную копию базы:

```bash
cp data/students.db backups/students_$(date +%F).db
```

---

## Полезные команды

Перекомпилировать проект:

```bash
python -m py_compile app/**/*.py
```

Запустить бота вручную:

```bash
python bot.py
```

---

Версия: **v1.0**