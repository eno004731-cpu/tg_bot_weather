############## библиотеки ##############
import asyncio
import requests

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
import datetime as dt
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
global response
response = requests.get(url, params=params)
global data
data = response.json()
print(data)
######## кнопки для бота ########
menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="погода"),
            KeyboardButton(text="ID чата"),
        ],
        [
            KeyboardButton(text="подсчет слов"),
            KeyboardButton(text="помощь"),
        ]
    ],
    resize_keyboard=True
)



########## получаем токен и создаем бота #########
load_dotenv()
Token = getenv('BOT_TOKEN')
bot = Bot(token=Token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

########## блок с ботом #########
@dp.message(CommandStart())
async def start(message: Message):
    await message.answer('Привет', reply_markup=menu)


@dp.message(Command("chatid",))
@dp.message(lambda message: message.text == "ID чата")
async def getChatId(message: Message):
    await message.answer(f'ID чата: {message.chat.id}')


@dp.message(Command("weather", 'погода'))
@dp.message(lambda message: message.text == "погода")
async def send_weather(message: Message):   
    global user_chat_id
    global data 
    global response
    response = requests.get(url, params=params)
    data = response.json()
    user_chat_id = message.chat.id
    await message.answer(f'Температура: {data["current"]["temperature_2m"]}°C' f'\nСкорость ветра: {data["current"]["wind_speed_10m"]} м/с' f'\nВремя: {data["current"]["time"]}')
    print(data)

@dp.message(Command("stop_send_weather",))
async def stop_send_weather(message: Message):
    global user_chat_id
    user_chat_id = None
    await message.answer("Отправка погоды остановлена")

@dp.message(Command("help", 'помощь'))
@dp.message(lambda message: message.text == "помощь")
async def send_help(message: Message):
    await message.answer("Список команд:\n"
    "/chatid - узнать ID чата\n"
    "/weather - узнать текущую погоду\n"
    "/stop_send_weather - остановить отправку погоды\n"
    "/Count_words - посчитать количество слов в сообщении\n"
    "/help - показать это сообщение")

class CountWords(StatesGroup):
    waiting_for_text = State()



@dp.message(Command("Count_words", 'подсчет слов'))
@dp.message(lambda message: message.text == "подсчет слов")
async def count_words_start(message: Message, state: FSMContext):
    await message.answer("Напиши текст, и я посчитаю количество слов в нём")
    await state.set_state(CountWords.waiting_for_text)

@dp.message(CountWords.waiting_for_text)
async def count_words_finish(message: Message, state: FSMContext):
    text = message.text
    word_count = len(text.split())-text.count('-')-text.count('--')
    await message.answer(f"Количество слов в вашем сообщении: {word_count}")
    await state.clear()
########## блок с scheduler #########

async def send_weather1():
    if user_chat_id is None:
        return 
    
    
async def send_weather2():   
    global data 
    global response
    response = requests.get(url, params=params)
    data = response.json()
    await bot.send_message(chat_id=user_chat_id,
                            text=f'Температура: {data["current"]["temperature_2m"]}°C' 
                            f'\nСкорость ветра: {data["current"]["wind_speed_10m"]} м/с' 
                            f'\nВремя: {data["current"]["time"]}')
    print(f'это функция которая отправляет погоду раз в 10 минут: {data}')



scheduler = AsyncIOScheduler(timezone='Europe/Moscow')


########### main ############
async def main():
    scheduler.add_job(send_weather2,"interval", minutes=10) # отправлять погоду каждый день в 9:00
    scheduler.start()
    print(scheduler)
    

    await dp.start_polling(bot)
if __name__ == '__main__':
    asyncio.run(main())

