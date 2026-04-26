from collections.abc import Callable
from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

from SQL import add_note, delete_note, get_notes


router = Router()
ScheduleReminderCallback = Callable[[int, str, datetime], None]
schedule_reminder_callback: ScheduleReminderCallback | None = None



def configure_reminder_scheduler(callback: ScheduleReminderCallback) -> None:
    global schedule_reminder_callback
    schedule_reminder_callback = callback

main_menu = ReplyKeyboardMarkup(
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

notes_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Добавить заметку"),
            KeyboardButton(text="Показать заметки"),
        ],
        [
            KeyboardButton(text="Удалить заметку"),
            KeyboardButton(text="Назад"),
        ],
    ],
    resize_keyboard=True,
)


class Notes(StatesGroup):
    waiting_for_action = State()
    waiting_for_writing_note = State()
    waiting_for_deletion = State()
    waiting_to_set_reminder = State()
    waiting_for_reminder = State()


@router.message(Command("notes"))
@router.message(lambda message: message.text == "Заметки")
async def notes_menu(message: Message, state: FSMContext):
    await message.answer("Здесь будут твои заметки", reply_markup=notes_menu_keyboard)
    await state.set_state(Notes.waiting_for_action)


@router.message(Notes.waiting_for_action)
async def notes_action(message: Message, state: FSMContext):
    text = message.text
    user_id = message.from_user.id

    if text == "Добавить заметку":
        await message.answer("Напиши текст заметки")
        await state.set_state(Notes.waiting_for_writing_note)
        return

    if text == "Показать заметки":
        notes_list = get_notes(user_id)

        if not notes_list:
            await message.answer("У тебя нет заметок.")
            return

        notes_text = "\n".join(
            f"{note_id}. {note} ({created_at})"
            for note_id, note, created_at in notes_list
        )
        await message.answer(f"Твои заметки:\n{notes_text}")
        return

    if text == "Удалить заметку":
        notes_list = get_notes(user_id)

        if not notes_list:
            await message.answer("У тебя нет заметок для удаления.")
            return

        notes_text = "\n".join(f"{note_id}. {note}" for note_id, note, _ in notes_list)
        await message.answer(
            "Напиши ID заметки, которую хочешь удалить:\n" + notes_text
        )
        await state.set_state(Notes.waiting_for_deletion)
        return

    if text == "Назад":
        await message.answer("Ты вернулся назад", reply_markup=main_menu)
        await state.clear()
        return

    await message.answer("Выбери действие кнопкой")


@router.message(Notes.waiting_for_writing_note)
async def handle_note_creation(message: Message, state: FSMContext):
    note = (message.text or "").strip()

    if not note:
        await message.answer("Отправь текст заметки")
        return

    await state.update_data(note_text=note)
    await message.answer("Нужно напоминание? Да или Нет")
    await state.set_state(Notes.waiting_for_reminder)


@router.message(Notes.waiting_for_reminder)
async def when_message(message: Message, state: FSMContext):
    answer = (message.text or "").strip().lower()

    if answer == "да":
        await message.answer("Введи время напоминания в формате ГГГГ-ММ-ДД ЧЧ:ММ")
        await state.update_data(with_reminder=True)
        await state.set_state(Notes.waiting_to_set_reminder)
        return

    elif answer == "нет":
        await state.update_data(with_reminder=False)
        data = await state.get_data()
        note_text = data["note_text"]
        add_note(message.from_user.id, note_text, None)
        await message.answer("Заметка добавлена!", reply_markup=notes_menu_keyboard)
        await state.set_state(Notes.waiting_for_action)
        return

    await message.answer("Пожалуйста, ответь Да или Нет.")


@router.message(Notes.waiting_to_set_reminder)
async def set_reminder(message: Message, state: FSMContext):
    raw_time = (message.text or "").strip()

    reminder_at = None
    for time_format in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            reminder_at = datetime.strptime(raw_time, time_format)
            break
        except ValueError:
                await state.set_state(Notes.waiting_for_action)
                return
                continue

    if reminder_at is None:
        await message.answer("Неверный формат времени. Используй ГГГГ-ММ-ДД ЧЧ:ММ")
        return

    if reminder_at <= datetime.now():
        await message.answer("Время напоминания должно быть в будущем.")
        return

    await state.update_data(reminder_at=reminder_at.isoformat())
    data = await state.get_data()
    note_text = data["note_text"]
    reminder_at_iso = data["reminder_at"]
    add_note(message.from_user.id, note_text, reminder_at_iso)

    if schedule_reminder_callback is not None:
        schedule_reminder_callback(message.chat.id, note_text, reminder_at)

    await message.answer(
        f"Заметка и напоминание сохранены на {reminder_at_iso}.",
        reply_markup=notes_menu_keyboard,
    )
    await state.set_state(Notes.waiting_for_action)


@router.message(Notes.waiting_for_deletion)
async def handle_note_deletion(message: Message, state: FSMContext):
    note_id = message.text

    if not note_id or not note_id.isdigit():
        await message.answer("Пожалуйста, отправь числовой ID заметки.")
        return

    deleted = delete_note(int(note_id), message.from_user.id)

    if not deleted:
        await message.answer("Заметка с таким ID не найдена.")
    else:
        await message.answer("Заметка удалена!")

    await state.set_state(Notes.waiting_for_action)
