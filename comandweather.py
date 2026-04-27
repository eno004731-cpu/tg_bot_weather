import requests
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from SQL import set_weather_notification_permission


router = Router()


class Weather(StatesGroup):
    waiting_for_weather = State()


url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": 55.809,
    "longitude": 37.958,
    "current": "temperature_2m,wind_speed_10m,weather_code",
    "timezone": "auto",
}


def get_weather_text() -> str:
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()["current"]
    return (
        f'Температура: {data["temperature_2m"]}°C'
        f'\nСкорость ветра: {data["wind_speed_10m"]} м/с'
        f'\nВремя: {data["time"]}'
    )


@router.message(Command("weather"))
@router.message(lambda message: message.text == "погода")
async def show_weather(message: Message, state: FSMContext):
    await message.answer(get_weather_text())
    await message.answer("Хотите ли вы получать ежедневные уведомления о погоде? (да/нет)")
    await state.set_state(Weather.waiting_for_weather)


@router.message(Weather.waiting_for_weather)
async def process_weather_notification_permission(message: Message, state: FSMContext):
    answer = (message.text or "").strip().lower()
    chat_id = message.chat.id

    if answer == "да":
        set_weather_notification_permission(chat_id, True)
        await message.answer("Вы будете получать ежедневные уведомления о погоде.")
        await state.clear()
        return

    if answer == "нет":
        set_weather_notification_permission(chat_id, False)
        await message.answer("Вы не будете получать ежедневные уведомления о погоде.")
        await state.clear()
        return

    await message.answer("Пожалуйста, ответьте 'да' или 'нет'.")
