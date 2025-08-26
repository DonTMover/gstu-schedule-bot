# load environment variables
from dotenv import load_dotenv
from os import getenv

# other imports
import re
from api import get_schedule
from groupes import groups
from loguru import logger

# aiogram imports
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

# from utils
from utils import get_inline_keyboard_select_group


load_dotenv()
TOKEN = getenv("BOT_TOKEN")

dp = Dispatcher()

#add logging
logger.add("bot.log", rotation="10 MB", retention="30 days", level="INFO")

@dp.message(CommandStart())
async def start(message: Message):
    logger.info(f"User {message.from_user.id} started bot")
    await message.answer(
        text="Привет, выбери группу, чтобы получить расписание.",
        reply_markup=get_inline_keyboard_select_group()
    )

@dp.message()
async def handler(message: Message):
    text = message.text.strip()
    logger.info(f"Received message: {text} from user {message.from_user.id}")


    match = re.search(r"Вы выбрали группу: (\S+)", text)
    print(match)
    if match:
        group_code = match.group(1)

        if group_code in groups:
            print(group_code)
            await message.answer(
                text=await get_schedule(group_code),
                #reply_markup=get_inline_keyboard()
            )




async def main():
    logger.info("Bot is starting polling...")
    bot = Bot(
        token=TOKEN,
        properties=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    await dp.start_polling(bot)

def run():
    import asyncio
    print("Starting bot...")
    load_dotenv()
    print(getenv("BOT_TOKEN"))
    asyncio.run(main())
    


if __name__ == "__main__":
    run()
