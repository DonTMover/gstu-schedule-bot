# load environment variables
from dotenv import load_dotenv
from os import getenv

# other imports
import hashlib
from typing import Dict, List

# aiogram imports
from aiogram import types
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup    

load_dotenv()
TOKEN = getenv("BOT_TOKEN")

dp = Dispatcher()


groups = {
    "АП-11": "ap-11",
    "АП-21": "ap-21",
    "АП-31": "ap-31",
    "АП-12": "ap-41",
    "АТ-11": "at-11",
    "АТ-21": "at-21",
    "АЭ-11": "ae-11",
    "АЭ-21": "ae-21",
    "АЭП-11": "aep-11",
}

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        text="Привет, выбери группу, чтобы получить расписание.",
        reply_markup=get_inline_keyboard_select_group()
    )

@dp.message()
async def handler(message: Message):
    pass

def get_inline_keyboard_select_group() -> InlineKeyboardMarkup:
    select_button = InlineKeyboardButton(
        text="Поиск",
        switch_inline_query_current_chat="",
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[select_button]])
    return keyboard

@dp.callback_query(lambda c: c.data == "search")
async def process_search(callback_query):
    await callback_query.message.answer("Please enter the group code (e.g., АП-11):")
    await callback_query.answer()


def get_inline_keyboard() -> InlineKeyboardMarkup:
    button1 = InlineKeyboardButton(text="Button 1", callback_data="button1")
    button2 = InlineKeyboardButton(text="Button 2", callback_data="button2")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button1, button2]])
    return keyboard

@dp.callback_query(lambda c: c.data == "button1")
async def process_button1(callback_query):
    await callback_query.message.answer("You clicked Button 1!")
    await callback_query.answer()
    
@dp.callback_query(lambda c: c.data == "button2")
async def process_button2(callback_query):
    await callback_query.message.answer("You clicked Button 2!")
    await callback_query.answer()

@dp.inline_query()
async def inline_handler(inline_query: types.InlineQuery):
    query = inline_query.query.strip()
    results = []

    if query:  # Чекаем что пользователь В ОБЩЕМ что то ввел 
        for key, value in groups.items():
            if query.lower() in key.lower():  #Ищем по подстроке
                result_id = hashlib.md5(key.encode()).hexdigest()
                input_content = types.InputTextMessageContent(
                    message_text=f"Вы выбрали группу: {key} ({value})"
                )
                result = types.InlineQueryResultArticle(
                    id=result_id,
                    title=f"Группа: {key}",
                    input_message_content=input_content,
                    description=f"Код группы: {value}"
                )
                results.append(result)

    # Если юзер даун и ввел че то что мы не знаем говорим ему что не найдено 
    if query and not results:
        result_id = hashlib.md5(query.encode()).hexdigest()
        input_content = types.InputTextMessageContent(
            message_text="Группа не найдена. Пожалуйста, введите корректный код группы."
        )
        result = types.InlineQueryResultArticle(
            id=result_id,
            title="Группа не найдена",
            input_message_content=input_content,
            description="Нет такой группы." #Еле сдержался от мата вхзввххвхв
        )
        results.append(result)

    await inline_query.answer(results, cache_time=1)


async def main():
    bot = Bot(
        token=TOKEN,
        properties=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
