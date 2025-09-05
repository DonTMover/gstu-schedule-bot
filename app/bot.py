# load environment variables
from dotenv import load_dotenv
from os import getenv

# other imports
import re
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
from aiogram.methods import EditMessageText

# from packages
from utils import (get_inline_keyboard_select, get_days_students_keyboard, get_inline_keyboard_disclaimer,
                   handle_group_search, handle_teacher_inline_search,get_teacher_rating_keyboard, 
                   handle_teacher_inline_search_names, get_human_readable_schedule, get_human_readable_teacher_schedule,
                   get_days_teacher_keyboard)
from api import fetch_schedule_cached, get_teacher_schedule_cached
from db import db
from cache import cache


load_dotenv()
TOKEN = getenv("BOT_TOKEN")

dp = Dispatcher()

#add logging
logger.add("bot.log", rotation="10 MB", retention="30 days", level="INFO")

user_teacher = {} # временное хранилище для выбранного преподавателя пользователем
user_week = {}    # временное хранилище для выбранной недели пользователем
user_day = {}     # временное хранилище для выбранного дня недели пользователем

@dp.message(CommandStart()) # Обрабатываем старт бота и записываем чела в группу
async def start(message: Message):
    logger.info(f"User {message.from_user.id} started bot")
    await message.answer( # TODO: добавить в дикслеймер еще ссылку на гитхаб
        text="Привет, сначала прочти дисклеймер. \n\n"
        "Этот бот не является официальным приложением ГГТУ и не связан с университетом. \n\n"
        "Автор не несет ответственности за возможные ошибки в расписании. \n\n"
        "Используя этот бот, вы соглашаетесь с тем, что вся информация предоставляется 'как есть' без каких-либо гарантий. \n\n"
        "Если вы не согласны с этими условиями, пожалуйста, не используйте этот бот.\n\n"
        "После принятия условий вы сможете выбрать свою группу и просматривать расписание, а также расписание преподавателей. \n\n"
        "Так-же данный бот OpenSource и вот ссылка на Github:https://github.com/DonTMover/gstu-schedule-bot",
        reply_markup=get_inline_keyboard_disclaimer()
    )

@dp.message()  # Главный обработчик который распределяет все
async def handler(message: Message):
    text = message.text.strip()
    logger.info(f"Received message: {text} from user {message.from_user.id}")

    # тестовая команда
    if text.lower() == "/test_get_id":
        await message.answer(f"Ваш ID: {message.from_user.id}")
        return

    # 1. ГРУППЫ
    match_group = re.search(r"Вы выбрали группу: (\S+)", text)
    logger.info(f"Regex match for group: {match_group}")
    if match_group:
        group_code = match_group.group(1)

        await db.set_group(message.from_user.id, group_code)
        logger.info(f"Database updated for user {message.from_user.id} with group {group_code}")

        if group_code in groups:
            logger.info(f"User {message.from_user.id} selected valid group {group_code}")
            await message.answer(
                text="Выберите день недели, чтобы увидеть расписание.",
                reply_markup=get_days_students_keyboard()
            )
        return

    # 2. РЕЙТИНГ ПРЕПОДАВАТЕЛЕЙ
    match_teacher_rating = re.search(
        r"Преподаватель: (.+)\n⭐\s*Рейтинг: ([0-5](?:\.[0-9]{1,2})?)/5",
        text
    )
    if match_teacher_rating:
        fullname = match_teacher_rating.group(1)
        current_rating = match_teacher_rating.group(2)
        logger.info(f"User {message.from_user.id} viewing teacher {fullname} with rating {current_rating}")

        if await db.user_exists(message.from_user.id):
            await db.ensure_user(message.from_user.id)
            await message.answer(
                text=f"Преподаватель: {fullname}\n⭐ Текущий рейтинг: {current_rating}/5",
                reply_markup=await get_teacher_rating_keyboard(fullname)
            )
        else:
            await message.answer(
                text="Сначала выберите группу, используя команду /start",
                reply_markup=get_inline_keyboard_select()
            )
        return

    # 3. РАСПИСАНИЕ ПРЕПОДАВАТЕЛЕЙ
    match_teacher_schedule = re.search(
        r"Преподаватель: (.+)$",  # только ФИО
        text
    )
    if match_teacher_schedule:

        fullname = match_teacher_schedule.group(1)
        logger.info(f"User {message.from_user.id} selected teacher {fullname} to view schedule")
        slug = await db.get_teacher_by_name(fullname)
        if not slug:
            await message.answer("Преподаватель не найден в базе.")
            return
        
        user_teacher[message.from_user.id] = {
        "full_name": fullname,
        "slug": slug
        }

        if await db.user_exists(message.from_user.id):
            await db.ensure_user(message.from_user.id)

            # try:
            #     teacher_schedule = await get_teacher_schedule_cached(slug)  
            # except NameError:
            #     teacher_schedule = "📅 Расписание пока недоступно."

            # data = get_human_readable_teacher_schedule(teacher_schedule)
            await message.answer(
                text="Выберите день недели, чтобы увидеть расписание.",
                reply_markup=get_days_teacher_keyboard()
            )
        else:
            await message.answer(
                text="Сначала выберите группу, используя команду /start",
                reply_markup=get_inline_keyboard_select()
            )
        return

@dp.callback_query(F.data.startswith("subgroup:"))
async def process_subgroup(callback: types.CallbackQuery):
    subgroup = int(callback.data.split(":")[1])
    
    # сохраняем в БД выбор пользователя
    await db.set_subgroup(callback.from_user.id, subgroup)
    logger.info(f"User {callback.from_user.id} selected subgroup {subgroup}")

    await callback.message.edit_text(
        f"✅ Ваша подгруппа: {subgroup}\nТеперь выберите день недели:",
        reply_markup=get_days_keyboard(for_teacher=False)
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("week:"))
async def select_week(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    action = callback.data.split(":")[1]  # prev или next


    from datetime import date, timedelta
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    if user_id not in user_week:
        user_week[user_id] = monday
    else:
        monday = user_week[user_id]

    # Сдвигаем неделю
    if action == "prev":
        monday -= timedelta(days=7)
    elif action == "next":
        monday += timedelta(days=7)
    user_week[user_id] = monday

    # Используем последний выбранный день пользователя, если есть
    selected_day_code = user_day.get(user_id, "MONDAY")

    class FakeCallback:
        def __init__(self, from_user, message, data):
            self.from_user = from_user
            self.message = message
            self.data = data
        async def answer(self):
            pass
    fake_callback = FakeCallback(callback.from_user, callback.message, f"day:{selected_day_code}")
    await day_schedule(fake_callback)

@dp.callback_query(lambda c: c.data == "search") # Для InlineSearch поиска группы
async def process_search(callback_query):
    await callback_query.message.answer("Please enter the group code (e.g., АП-11):")
    await callback_query.answer()
    
@dp.callback_query(lambda c: c.data == "disclaimer:accept") # Обработка принятия дисклеймера
async def process_disclaimer(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text(
        text="Спасибо за принятие условий. Теперь вы можете выбрать группу.",
        reply_markup=get_inline_keyboard_select()
    )
    await callback_query.answer("Вы приняли условия.")

@dp.message(Command("test_get_id")) # тестовая команда попавшая на прод :3
async def schedule_cmd(message: types.Message):
    await message.answer(f"Ваш ID: {message.from_user.id}")

@dp.inline_query()
async def inline_handler(inline_query: types.InlineQuery):
    query = inline_query.query.strip()
    results = []

    if query.startswith("teacher:"):
        results = await handle_teacher_inline_search(query.replace("teacher:", "").strip())

    elif query.startswith("group:"):
        results = handle_group_search(query.replace("group:", "").strip())

    elif query.startswith("teacher_schedule:"):
        results = await handle_teacher_inline_search_names(query.replace("teacher_schedule:", "").strip())

    await inline_query.answer(results, cache_time=1)

@dp.callback_query(F.data.startswith("rate:")) # Обработка оценок
async def rate_teacher(callback: types.CallbackQuery):
    _, hash_id, value_str = callback.data.split(":")
    value = int(value_str)

    # Находим имя преподавателя по хешу через новый метод
    name = await db.get_teacher_name_by_hash(hash_id)
    if not name:
        await callback.answer("Преподаватель не найден!", show_alert=True)
        return

    avg, count = await db.add_teacher_rating(name, value, callback.from_user.id)

    text = f"Преподаватель: {name}\n⭐ Рейтинг: {avg:.2f}/5\nКоличество оценок: {count}"
    keyboard = await get_teacher_rating_keyboard(name)

    if callback.message:  # обычное сообщение
        await callback.message.edit_text(text, reply_markup=keyboard)
    elif callback.inline_message_id:  # inline-сообщение
        await EditMessageText(
            text=text,
            inline_message_id=callback.inline_message_id,
            reply_markup=keyboard,
            parse_mode="HTML"
        ).send(callback.bot)

    await callback.answer(f"Вы установили {value}⭐!")


@dp.callback_query(lambda c: c.data == "comeback") # Возврат к началу
async def comeback(callback: types.CallbackQuery):
    await callback.message.edit_text(
        text="Выберите группу снова или перейдите в другой раздел.",
        reply_markup=get_inline_keyboard_select()
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("teacher_day:"))
async def teacher_day_schedule(callback: types.CallbackQuery):
    code = callback.data.split(":")[1]  # 'MONDAY', 'TUESDAY', ...
    days_map = {
        "MONDAY": "Понедельник",
        "TUESDAY": "Вторник",
        "WEDNESDAY": "Среда",
        "THURSDAY": "Четверг",
        "FRIDAY": "Пятница",
        "SATURDAY": "Суббота",
    }
    day_name = days_map.get(code, code)

    # Получаем выбранного пользователем преподавателя из user_teacher
    teacher_info = user_teacher.get(callback.from_user.id)
    if not teacher_info:
        await callback.message.edit_text(
            "Сначала выберите преподавателя.",
            reply_markup=get_inline_keyboard_select()
        )
        await callback.answer()
        return

    teacher_slug = teacher_info.get("slug")
    teacher_fullname = teacher_info.get("full_name")

    try:
        data = await get_teacher_schedule_cached(teacher_slug)
        schedule = get_human_readable_teacher_schedule(data)
        lessons = schedule.get(day_name, [])
    except Exception as e:
        logger.error(f"Error fetching schedule for {teacher_fullname}: {e}")
        await callback.message.edit_text("📅 Расписание пока недоступно.")
        await callback.answer()
        return

    # Вспомогатель для времени
    def t(v: str | None) -> str:
        if not v:
            return "-"
        return v[:5]  # 'HH:MM'

    from datetime import date, timedelta, datetime as _dt
    if lessons:
        day_date_iso = lessons[0].get("date")
        week_type = lessons[0].get("weekType") or "-"
    else:
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        shift = ["MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY","SATURDAY","SUNDAY"].index(code)
        day_date_iso = (monday + timedelta(days=shift)).isoformat()
        week_type = "EVEN" if today.isocalendar().week % 2 == 0 else "ODD"

    try:
        day_date_str = _dt.fromisoformat(day_date_iso).strftime("%d.%m.%Y")
    except Exception:
        day_date_str = day_date_iso

    if not lessons:
        text = f"📅 {day_name}, {day_date_str}  •  Неделя: <b>{week_type}</b>\n\nЗанятий нет 🎉"
    else:
        parts = [f"📅 {day_name}, {day_date_str}  •  Неделя: <b>{week_type}</b>\n"]
        for i, lesson in enumerate(lessons, 1):
            parts.append(
                f"<b>{lesson.get('lessonNumber')}. {lesson.get('subject') or '—'}</b>"
                f" ({lesson.get('subjectShort') or ''})\n"
                f"🕒 {t(lesson.get('startTime'))} – {t(lesson.get('endTime'))}\n"
                f"👥 Группы: {lesson.get('groups') or '-'}\n"
                f"🏫 Кабинет: {lesson.get('classrooms') or '-'}\n"
            )
        text = "\n".join(parts)

    await callback.message.edit_text(
        text,
        reply_markup=get_days_teacher_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()





@dp.callback_query(F.data.startswith("day:"))  # Получение расписания на определенный день недели и его форматирование
async def day_schedule(callback: types.CallbackQuery):
    code = callback.data.split(":")[1]   # 'MONDAY', 'TUESDAY', ...
    user_day[callback.from_user.id] = code
    days_map = {
        "MONDAY": "Понедельник",
        "TUESDAY": "Вторник",
        "WEDNESDAY": "Среда",
        "THURSDAY": "Четверг",
        "FRIDAY": "Пятница",
        "SATURDAY": "Суббота",
        "SUNDAY": "Воскресенье",
    }
    day_name = days_map.get(code, code)

    try:
        user_group = await db.get_group(callback.from_user.id)
        if not user_group:
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

    # Получаем расписание на ТЕКУЩУЮ неделю (функция уже фильтрует по startDate этой недели и добавляет date/weekType)

    raw = await fetch_schedule_subgroup_cached(user_group, subgroup=await db.get_subgroup(callback.from_user.id) or 1)
    schedule = get_human_readable_schedule(raw,monday=user_week.get(callback.from_user.id))

    lessons = schedule.get(day_name, [])
    logger.info(f"Fetched schedule for user {callback.from_user.id} for {day_name}")

    # Определим дату выбранного дня и чётность недели для заголовка
    # (берём из первой пары; если пар нет — вычислим дату этого дня недели от сегодняшнего понедельника)
    from datetime import date, timedelta
    if lessons:
        day_date_iso = lessons[0].get("date")  # 'YYYY-MM-DD'
        week_type = lessons[0].get("weekType") or "-"
    else:
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        shift = ["MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY","SATURDAY","SUNDAY"].index(code)
        day_date_iso = (monday + timedelta(days=shift)).isoformat()
        week_type = "EVEN" if today.isocalendar().week % 2 == 0 else "ODD"

    # Красивое отображение даты
    try:
        from datetime import datetime as _dt
        day_date_str = _dt.fromisoformat(day_date_iso).strftime("%d.%m.%Y")
    except Exception:
        day_date_str = day_date_iso

    # Вспомогатель для времени
    def t(v: str | None) -> str:
        # ожидаем 'HH:MM:SS' или 'HH:MM'
        if not v:
            return "-"
        return v[:5]  # 'HH:MM'

    if not lessons:
        text = f"📅 {day_name}, {day_date_str}  •  Неделя: <b>{week_type}</b>\n\nЗанятий нет 🎉"
    else:
        parts = [f"📅 {day_name}, {day_date_str}  •  Неделя: <b>{week_type}</b>\n"]
        for i, lesson in enumerate(lessons, 1):
            parts.append(
                f"<b>{lesson.get('lessonNumber')}. {lesson.get('subject') or '—'}</b>"
                f" ({lesson.get('subjectShort') or ''})\n"
                f"🕒 {t(lesson.get('startTime'))} – {t(lesson.get('endTime'))}\n"
                f"👨‍🏫 {lesson.get('teachers') or '-'}\n"
                f"🏫 {lesson.get('classrooms') or '-'}\n"
                f"👥 {lesson.get('groups') or '-'}\n"
            )
        text = "\n".join(parts)

    # Проверка: если текст и кнопки не изменились, не вызываем edit_text
    current_text = callback.message.text or ""
    current_markup = callback.message.reply_markup
    new_markup = get_days_keyboard(for_teacher=False)
    if text == current_text and (current_markup == new_markup or current_markup is None):
        await callback.answer()
        return

    await callback.message.edit_text(
        text,
        reply_markup=new_markup,
        parse_mode="HTML"
    )
    await callback.answer()




async def main():
    logger.info("Bot is starting polling...")
    bot = Bot(
        token=TOKEN,
        properties=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    await db.init()
    await cache.init()  # Инициализируем пул соединений с БД

    await dp.start_polling(bot)

def run():
    import asyncio
    logger.info("Starting bot...")
    load_dotenv()
    #print(getenv("BOT_TOKEN"))
    
    asyncio.run(main())
    


if __name__ == "__main__":
    run()
