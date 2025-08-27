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

# from packages
from utils import get_inline_keyboard_select_group, get_days_keyboard, days_map
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

@dp.inline_query()
async def inline_handler(inline_query: types.InlineQuery):
    query = inline_query.query.strip()
    logger.info(f"Inline query: '{query}' from user {inline_query.from_user.id}")

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

@dp.message(Command("schedule"))
async def schedule_cmd(message: types.Message):
    await message.answer(
        "Выберите день недели:",
        reply_markup=get_days_keyboard()
    )


@dp.callback_query(F.data.startswith("day:"))
async def day_schedule(callback: types.CallbackQuery):
    code = callback.data.split(":")[1]   # MONDAY, TUESDAY ...
    day_name = days_map[code]
    try:
        if not db.get_group(callback.from_user.id):
            await callback.message.edit_text(
                "Сначала выберите группу, используя команду /start",
                reply_markup=get_inline_keyboard_select_group()
            )
            await callback.answer()
            return
    except Exception as e:
        logger.error(f"Error fetching group for user {callback.from_user.id}: {e}")
        await callback.message.edit_text(
            "Произошла ошибка при получении вашей группы. Пожалуйста, попробуйте снова.",
            reply_markup=get_inline_keyboard_select_group()
        )
        await callback.answer()
        return
    
    schedule = get_human_readable_schedule(await fetch_schedule(db.get_group(callback.from_user.id)))  
    lessons = schedule[day_name]
    logger.info(f"Fetched schedule for user {callback.from_user.id} for {day_name}: {lessons}")

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
