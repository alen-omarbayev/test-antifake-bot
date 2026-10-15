from datetime import datetime
from itertools import count
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram import Dispatcher
from aiogram.methods import EditMessageReplyMarkup, SendMessage
from aiogram.types import CallbackQuery, Chat, Message, Update
from aiogram.types import User as TgUser

from bot.handlers.menu import menu_router
from bot.handlers.serial_check import serial_router
from bot.handlers.start import start_router
from bot.models.user import User
from bot.services.serial_check_service import SerialCheckResult
from bot.stores import format_stores
from bot.texts import CHOOSE_LANGUAGE_TEXT, LANG_RU, LANG_TJ, TEXTS

TG_IDS = count(1000)


@pytest.fixture(scope="module")
def dp():
    # Routers are module-level singletons and can be attached to only one parent.
    dispatcher = Dispatcher()
    dispatcher.include_routers(start_router, menu_router, serial_router)
    return dispatcher


@pytest.fixture(autouse=True)
def no_analytics():
    with patch("bot.handlers.start.AnalyticsTracker") as start_tracker, patch(
        "bot.handlers.serial_check.AnalyticsTracker"
    ) as check_tracker:
        start_tracker.return_value.track_bot_started = AsyncMock()
        check_tracker.return_value.track_serial_check_started = AsyncMock()
        yield


def make_user(language: str | None) -> User:
    # A fresh Telegram id per user keeps the serial throttling cooldown from leaking between tests.
    return User(id=1, telegram_id=next(TG_IDS), username="tester", language=language)


def make_message(user: User, text: str | None = None) -> Message:
    return Message(
        message_id=1,
        date=datetime.now(),
        chat=Chat(id=user.telegram_id, type="private"),
        from_user=TgUser(id=user.telegram_id, is_bot=False, first_name="Tester"),
        text=text,
    )


@pytest.fixture
def feed(dp, bot):
    async def _feed(user: User, text: str | None = None, data: str | None = None, session=None):
        message = make_message(user, text)
        if data is None:
            update = Update(update_id=1, message=message)
        else:
            callback = CallbackQuery(
                id="cb",
                from_user=message.from_user,
                chat_instance="ci",
                message=message,
                data=data,
            )
            update = Update(update_id=1, callback_query=callback)
        bot.calls.clear()
        await dp.feed_update(bot, update, session=session or MagicMock(), user=user)
        return [call for call in bot.calls if isinstance(call, (SendMessage, EditMessageReplyMarkup))]

    return _feed


def button_texts(call) -> list[str]:
    return [button.text for row in call.reply_markup.inline_keyboard for button in row]


def test_languages_have_same_text_keys():
    assert TEXTS[LANG_RU].keys() == TEXTS[LANG_TJ].keys()


async def test_start_asks_for_language(feed):
    [reply] = await feed(make_user(None), text="/start")

    assert reply.text == CHOOSE_LANGUAGE_TEXT
    assert button_texts(reply) == ["Русский", "Таджикский"]


async def test_choosing_language_saves_it_and_sends_greeting_and_menu(feed):
    user = make_user(None)
    session = MagicMock()
    session.execute = AsyncMock()

    edit, greeting, menu = await feed(user, data="lang:tj", session=session)

    assert user.language == LANG_TJ
    session.execute.assert_awaited_once()
    assert edit.reply_markup is None
    assert greeting.text == TEXTS[LANG_TJ]["greeting"]
    assert menu.text == TEXTS[LANG_TJ]["choose_section"]
    assert button_texts(menu) == [
        "Санҷиши аслияти маҳсулот",
        "Мағозаҳои расмии LG",
        "Сомонаи расмии LG Electronics",
    ]


async def test_main_menu_button(feed):
    [menu] = await feed(make_user(LANG_RU), data="menu:main")

    assert menu.text == "Выберите интересующий вас раздел:"


async def test_stores_button_shows_city_buttons(feed):
    [edit] = await feed(make_user(LANG_TJ), data="menu:stores")

    assert button_texts(edit) == ["Душанбе", "Хуҷанд"]


@pytest.mark.parametrize("lang", [LANG_RU, LANG_TJ])
async def test_city_button_lists_stores(feed, lang):
    [reply] = await feed(make_user(lang), data="stores:khujand")

    assert reply.text == format_stores("khujand", lang)


def test_store_list_formats():
    assert format_stores("khujand", LANG_RU) == (
        "Худжанд:\n"
        "1. Mechta — ул. Исмоила Сомони, 10 — 92 444 88 22 — 09:00–19:00\n"
        "2. Mechta — ул. Исмоила Сомони, 53 — 92 444 88 22 — 09:00–19:00\n"
        "3. Avrang — проспект И. Сомони, 9 — 98 999 78 17 — 08:00–19:00"
    )
    tj = format_stores("dushanbe", LANG_TJ)
    assert tj.startswith("Мағозаҳои расмии LG дар Душанбе\n\nAvrang\nСуроға: кӯчаи Ҷаббора Расулова, 9\n")
    assert tj.count("Соатҳои корӣ:") == 9


async def test_site_button(feed):
    [reply] = await feed(make_user(LANG_RU), data="menu:site")

    assert reply.text == TEXTS[LANG_RU]["site"]
    assert "https://lge.tj" in reply.text


async def test_service_button(feed):
    [reply] = await feed(make_user(LANG_TJ), data="menu:service")

    assert reply.text.startswith("Маркази хизматрасонии LG: 2225.")


async def test_check_button_sends_instructions(feed):
    [reply] = await feed(make_user(LANG_RU), data="menu:check")

    assert reply.text == TEXTS[LANG_RU]["check_instructions"]


def check_result(found: bool) -> SerialCheckResult:
    return SerialCheckResult(
        found=found, is_active=found or None, normalized_serial="ABC123", batch_id=None
    )


async def test_found_serial_gets_success_text_without_buttons(feed):
    with patch("bot.handlers.serial_check.SerialCheckService") as service_cls:
        service_cls.return_value.check = AsyncMock(return_value=check_result(True))
        [reply] = await feed(make_user(LANG_TJ), text="abc123")

    assert reply.text == TEXTS[LANG_TJ]["check_success"]
    assert reply.reply_markup is None


async def test_unknown_serial_gets_failure_text_and_buttons(feed):
    with patch("bot.handlers.serial_check.SerialCheckService") as service_cls:
        service_cls.return_value.check = AsyncMock(return_value=check_result(False))
        [reply] = await feed(make_user(None), text="abc123")

    # No language chosen yet: Russian by default.
    assert reply.text.startswith(TEXTS[LANG_RU]["check_failed"])
    assert reply.text.endswith(TEXTS[LANG_RU]["service_center"])
    assert button_texts(reply) == [
        "Проверить еще раз",
        "Связаться с сервисным центром",
        "Главное меню",
    ]
