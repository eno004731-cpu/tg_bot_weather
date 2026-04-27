import asyncio
import logging
from datetime import datetime
from os import getenv

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

from SQL import get_weather_subscribers, set_weather_notification_permission

from comandweather import get_weather_text, router as weather_router
from notes import configure_reminder_scheduler, router as notes_router
from countWords import router as count_words_router


menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="погода"),
            KeyboardButton(text="ID чата"),
        ],
        [
            KeyboardButton(text="подсчет слов"),
            KeyboardButton(text="помощь"),
        ],
        [
            KeyboardButton(text="Заметки"),
        ],
    ],
    resize_keyboard=True,
)

load_dotenv()
token = getenv("BOT_TOKEN")

if not token:
    raise RuntimeError("BOT_TOKEN is not set")

bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone="Europe/Moscow")


class CountWords(StatesGroup):
    waiting_for_text = State()


async def send_note_reminder(chat_id: int, note_text: str):
    await bot.send_message(chat_id=chat_id, text=f"Напоминание: {note_text}")


def schedule_note_reminder(chat_id: int, note_text: str, reminder_at: datetime) -> None:
    scheduler.add_job(
        send_note_reminder,
        "date",
        run_date=reminder_at,
        args=[chat_id, note_text],
    )


async def send_scheduled_weather():
    try:
        weather_text = get_weather_text()
    except Exception:
        logging.exception("Не удалось получить погоду для автоматической отправки")
        return

    for chat_id in get_weather_subscribers():
        try:
            await bot.send_message(chat_id=chat_id, text=weather_text)
        except Exception:
            logging.exception("Не удалось отправить погоду в chat_id=%s", chat_id)

configure_reminder_scheduler(schedule_note_reminder)
dp.include_router(notes_router)
dp.include_router(weather_router)
dp.include_router(count_words_router)


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Привет", reply_markup=menu)


@dp.message(Command("chatid"))
@dp.message(lambda message: message.text == "ID чата")
async def get_chat_id(message: Message):
    await message.answer(f"ID чата: {message.chat.id}")


@dp.message(Command("stop_send_weather"))
async def stop_send_weather(message: Message):
    set_weather_notification_permission(message.chat.id, False)
    await message.answer("Отправка погоды остановлена")


@dp.message(Command("help", "помощь"))
@dp.message(lambda message: message.text == "помощь")
async def send_help(message: Message):
    await message.answer(
        "Список команд:\n"
        "/chatid - узнать ID чата\n"
        "/weather - узнать текущую погоду\n"
        "/stop_send_weather - остановить отправку погоды\n"
        "/Count_words - посчитать количество слов в сообщении\n"
        "/notes - открыть заметки\n"
        "/help - показать это сообщение"
    )





async def main():
    logging.basicConfig(level=logging.INFO)
    scheduler.add_job(send_scheduled_weather, "interval", minutes=10)
    scheduler.start()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
