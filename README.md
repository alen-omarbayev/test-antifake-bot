# LG Serial Number Verification Bot

Telegram-бот для проверки серийного номера товара по базе PostgreSQL.

## Функционал (MVP)

- `/start` → приветствие + кнопка «Проверить серийный номер»
- Пользователь отправляет серийный номер → бот ищет его в PostgreSQL и отвечает,
  найден он или нет
- Event Tracking: `bot_started`, `serial_check_started`, `serial_check_success`, `serial_check_failed`
- Массовый импорт серийных номеров из CSV через отдельный CLI-скрипт

## Стек

Python, aiogram 3, PostgreSQL, SQLAlchemy 2, Alembic, asyncpg, python-dotenv.

## Установка

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt   # или requirements.txt для прод-окружения
cp .env.example .env                  # заполнить BOT_TOKEN и DATABASE_URL
```

## Миграции

```bash
alembic upgrade head
```

## Запуск бота

```bash
python -m bot.main
```

## Импорт серийных номеров из CSV

CSV с одной колонкой `serial_number` (опционально — `batch_id`):

```bash
python -m scripts.import_serials path/to/file.csv
```

Импорт идемпотентен: повторный запуск с тем же файлом не создаёт дублей.

## Тесты

```bash
pytest
```

## Структура проекта

```
bot/
├── main.py            # точка входа
├── config/            # чтение .env
├── models/            # SQLAlchemy-модели
├── repositories/       # доступ к БД
├── services/           # бизнес-логика
├── analytics/           # event tracking
├── handlers/            # обработчики Telegram
├── keyboards/            # клавиатуры
├── middlewares/          # throttling и др.
└── db/                   # engine/сессии

scripts/import_serials.py  # CLI-импорт CSV
migrations/                 # Alembic
tests/                       # unit-тесты
```
