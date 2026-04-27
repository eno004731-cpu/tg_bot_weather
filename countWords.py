from collections.abc import Callable
from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

router = Router()

class CountWords(StatesGroup):
    waiting_for_text = State()  


@router.message(Command("Count_words", "подсчет слов"))
@router.message(lambda message: message.text == "подсчет слов")
async def count_words_start(message: Message, state: FSMContext):
    await message.answer("Напиши текст, и я посчитаю количество слов в нём")
    await state.set_state(CountWords.waiting_for_text)


@router.message(CountWords.waiting_for_text)
async def count_words_finish(message: Message, state: FSMContext):
    text = (message.text or "").strip()

    if not text:
        await message.answer("Отправь текст сообщением")
        return

    word_count = len(text.split()) - text.count("-") - text.count("--")
    await message.answer(f"Количество слов в вашем сообщении: {word_count}")
    await state.clear()