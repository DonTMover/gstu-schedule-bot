# load environment variables
from dotenv import load_dotenv
from os import getenv

# aiogram imports
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup    

load_dotenv()
TOKEN = getenv("BOT_TOKEN")

dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        text=html.bold("Hello! This is a bot for viewing the schedule of GSTU."),
        reply_markup=get_inline_keyboard()
    )

@dp.message()
async def handler(message: Message):
    pass


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

async def main():
    bot = Bot(
        token=TOKEN,
        properties=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
