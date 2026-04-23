############## библиотеки ##############
import asyncio
import requests

from os import getenv
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

######### блок с погодой #########
url ="https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": 55.809,
    "longitude": 37.958,
    "current":"temperature_2m,wind_speed_10m,weather_code",
    'timezone': 'auto'

}
response = requests.get(url, params=params)
data = response.json()
print(data)




########## получаем токен и создаем бота #########
load_dotenv()
Token = getenv('BOT_TOKEN')
bot = Bot(token=Token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

########## блок с ботом #########
@dp.message(CommandStart())
async def start(message: Message):
    await message.answer('Привет')

@dp.message(lambda message: message.text == "/chatid")
async def getChatId(message: Message):
    await message.answer(f'ID чата: {message.chat.id}')

@dp.message(lambda message: message.text == "/weather")
async def send_weather(message: Message):   
    await bot.send_message(chat_id=message.chat.id, text=f"Температура: {data['current_weather']['temperature_2m']}°C\nСкорость ветра: {data['current_weather']['wind_speed_10m']} м/с\nКод погоды: {data['current_weather']['weather_code']}")

@dp.message(lambda message: message.text == "/help")
async def send_help(message: Message):
    await message.answer("Список команд:\n/chatid - узнать ID чата\n/weather - узнать текущую погоду\n/help - показать это сообщение")

########## блок с scheduler #########
scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
scheduler.add_job(send_weather, 'cron', hour=7, minute=10) # отправлять погоду каждый день в 9:00




########### main ############
async def main():
    await dp.start_polling(bot)
if __name__ == '__main__':
    asyncio.run(main())

