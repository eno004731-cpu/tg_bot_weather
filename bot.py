import asyncio
import logging
from datetime import datetime
from os import getenv

import requests
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from notes import configure_reminder_scheduler, router as notes_router


url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": 55.809,
    "longitude": 37.958,
    "current": "temperature_2m,wind_speed_10m,weather_code",
    "timezone": "auto",
}

user_chat_id: int | None = None

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


async def send_note_reminder(chat_id: int, note_text: str):
    await bot.send_message(chat_id=chat_id, text=f"Напоминание: {note_text}")


def schedule_note_reminder(chat_id: int, note_text: str, reminder_at: datetime) -> None:
    scheduler.add_job(
        send_note_reminder,
        "date",
        run_date=reminder_at,
        args=[chat_id, note_text],
    )


configure_reminder_scheduler(schedule_note_reminder)
dp.include_router(notes_router)


def get_weather_text() -> str:
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()["current"]
    return (
        f'Температура: {data["temperature_2m"]}°C'
        f'\nСкорость ветра: {data["wind_speed_10m"]} м/с'
        f'\nВремя: {data["time"]}'
    )


@dp.message(CommandStart())
async def start(message: Message):
    global user_chat_id
    user_chat_id = message.chat.id
    await message.answer("Привет", reply_markup=menu)


@dp.message(Command("chatid"))
@dp.message(lambda message: message.text == "ID чата")
async def get_chat_id(message: Message):
    await message.answer(f"ID чата: {message.chat.id}")


@dp.message(Command("weather", "погода"))
@dp.message(lambda message: message.text == "погода")
async def send_weather(message: Message):
    global user_chat_id
    user_chat_id = message.chat.id

    try:
        await message.answer(get_weather_text())
    except requests.RequestException:
        await message.answer("Не удалось получить погоду. Попробуй позже.")


@dp.message(Command("stop_send_weather"))
async def stop_send_weather(message: Message):
    global user_chat_id
    user_chat_id = None
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


class CountWords(StatesGroup):
    waiting_for_text = State()


@dp.message(Command("Count_words", "подсчет слов"))
@dp.message(lambda message: message.text == "подсчет слов")
async def count_words_start(message: Message, state: FSMContext):
    await message.answer("Напиши текст, и я посчитаю количество слов в нём")
    await state.set_state(CountWords.waiting_for_text)


@dp.message(CountWords.waiting_for_text)
async def count_words_finish(message: Message, state: FSMContext):
    text = (message.text or "").strip()

    if not text:
        await message.answer("Отправь текст сообщением")
        return

    word_count = len(text.split()) - text.count("-") - text.count("--")
    await message.answer(f"Количество слов в вашем сообщении: {word_count}")
    await state.clear()


async def send_scheduled_weather():
    if user_chat_id is None:
        return

    try:
        await bot.send_message(chat_id=user_chat_id, text=get_weather_text())
    except requests.RequestException:
        print("Не удалось получить погоду для автоматической отправки")



async def main():
    scheduler.add_job(send_scheduled_weather, "interval", minutes=10)
    scheduler.start()
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
