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

## Загрузка номеров через Telegram

Для админов из `ADMIN_IDS`:

- `/import` — включает режим загрузки и присылает инструкцию. Всем номерам
  сеанса проставляется партия вида `tg-20260928-1430` (местное время).
- Номера можно отправлять сообщениями (по одному в строке, через запятую или
  пробел) или файлом Excel `.xlsx` до 20 МБ: номера в первой колонке либо в колонке
  с заголовком `serial_number`; необязательная колонка `batch_id` важнее
  автоматической партии.
- По каждой загрузке бот отвечает, сколько добавлено, сколько уже было в базе,
  сколько повторов и некорректных номеров.
- `/done` — итог сеанса и выход, `/cancel` — выход без итога.

## Аналитика

Отчёт: пользователи (всего/новые), запуски `/start`, проверки (успешные/неуспешные
с причиной) и разбивка по дням. Границы дней считаются в `REPORT_TIMEZONE`
(по умолчанию `Asia/Dushanbe`).

```bash
python -m scripts.analytics_report --days 30   # по умолчанию 7, максимум 365
```

В боте: `/stats [дни]` (по умолчанию 7, максимум 90). Команда доступна только
пользователям из `ADMIN_IDS` в `.env` (Telegram id через запятую), остальным бот
не отвечает.

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
