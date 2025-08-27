# load environment variables
from dotenv import load_dotenv
from os import getenv

# other imports
import re
from api import get_schedule
from groupes import groups
from loguru import logger
import hashlib


# aiogram imports
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram import F
from aiogram.types import Message
from aiogram import types
from aiogram.types import InlineQuery

# from packages
from utils import (get_inline_keyboard_select, get_days_keyboard, days_map,
                   handle_group_search, handle_teacher_search,get_teacher_rating_keyboard)
from api import get_human_readable_schedule, fetch_schedule
from db import db


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
        reply_markup=get_inline_keyboard_select()
    )

@dp.message()
async def handler(message: Message):
    text = message.text.strip()
    logger.info(f"Received message: {text} from user {message.from_user.id}")


    match = re.search(r"Вы выбрали группу: (\S+)", text)
    print(match)
    if match:
        group_code = match.group(1)
        print(group_code)

        db.set_group(message.from_user.id, group_code)
        logger.info(f"Set group {group_code} for user {message.from_user.id}")

        if group_code in groups:
            print(group_code)
            await message.answer(
                text="Выберете день недели, чтобы увидеть расписание.",
                reply_markup=get_days_keyboard()
            )

@dp.callback_query(lambda c: c.data == "search")
async def process_search(callback_query):
    await callback_query.message.answer("Please enter the group code (e.g., АП-11):")
    await callback_query.answer()
    


@dp.message(Command("schedule"))
async def schedule_cmd(message: types.Message):
    await message.answer(
        "Выберите день недели:",
        reply_markup=get_days_keyboard()
    )

@dp.inline_query()
@dp.inline_query()
async def inline_handler(inline_query: types.InlineQuery):
    query = inline_query.query.strip()
    results = []

    if query.startswith("group:"):
        results = handle_group_search(query.replace("group:", "").strip())
    elif query.startswith("teacher:"):
        search = query.replace("teacher:", "").strip().lower()
        for name in db.teachers.keys():
            if search in name.lower():
                rating = db.get_teacher_rating(name)
                result_id = hashlib.md5(name.encode()).hexdigest()
                input_content = types.InputTextMessageContent(
                    message_text=f"Преподаватель: {name}\n⭐ Рейтинг: {rating}/5"
                )
                result = types.InlineQueryResultArticle(
                    id=result_id,
                    title=name,
                    input_message_content=input_content,
                    description=f"Текущий рейтинг: {rating}/5"
                )
                results.append(result)

    await inline_query.answer(results, cache_time=1)

@dp.callback_query(lambda c: c.data.startswith("rate:"))
async def rate_teacher(callback: types.CallbackQuery):
    data = callback.data.split(":")  # ["rate", "Имя", "звезды"]
    name = data[1]
    value = int(data[2])
    new_rating = db.add_teacher_rating(name, value)
    await callback.message.edit_text(
        f"Преподаватель: {name}\n⭐ Рейтинг: {new_rating}/5",
        reply_markup=get_teacher_rating_keyboard(name)
    )
    await callback.answer(f"Вы установили {new_rating}⭐!")

@dp.callback_query(F.data.startswith("day:"))
async def day_schedule(callback: types.CallbackQuery):
    code = callback.data.split(":")[1]   # MONDAY, TUESDAY ...
    day_name = days_map[code]
    try:
        if not db.get_group(callback.from_user.id):
            await callback.message.edit_text(
                "Сначала выберите группу, используя команду /start",
                reply_markup=get_inline_keyboard_select()
            )
            await callback.answer()
            return
    except Exception as e:
        logger.error(f"Error fetching group for user {callback.from_user.id}: {e}")
        await callback.message.edit_text(
            "Произошла ошибка при получении вашей группы. Пожалуйста, попробуйте снова.",
            reply_markup=get_inline_keyboard_select()
        )
        await callback.answer()
        return
    
    schedule = get_human_readable_schedule(await fetch_schedule(db.get_group(callback.from_user.id)))  
    lessons = schedule[day_name]
    logger.info(f"Fetched schedule for user {callback.from_user.id} for {day_name}")

    if not lessons:
        text = f"📅 {day_name}\n\nЗанятий нет 🎉"
    else:
        parts = [f"📅 {day_name}\n"]
        for i, lesson in enumerate(lessons, 1):
            parts.append(
                f"<b>{i}. {lesson['subject']}</b> ({lesson['subjectShort'] or ''})\n"
                f"🕒 {lesson['startTime']} – {lesson['endTime']}\n"
                f"👨‍🏫 {lesson['teachers'] or '-'}\n"
                f"🏫 {lesson['classrooms'] or '-'}\n"
                f"👥 {lesson['groups'] or '-'}\n"
            )
        text = "\n".join(parts)

    await callback.message.edit_text(
        text,
        reply_markup=get_days_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()



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
