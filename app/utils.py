from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent
)
from loguru import logger  
from aiogram import types
from groupes import groups
import hashlib

from db import db

days_map = { # дни
    "MONDAY": "Понедельник",
    "TUESDAY": "Вторник",
    "WEDNESDAY": "Среда",
    "THURSDAY": "Четверг",
    "FRIDAY": "Пятница",
    "SATURDAY": "Суббота"
}

def get_inline_keyboard_disclaimer() -> InlineKeyboardMarkup:
    disclaimer_button = InlineKeyboardButton(
        text="Принять",
        callback_data="disclaimer:accept"
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[disclaimer_button]]
    )
    return keyboard


def get_inline_keyboard_select() -> InlineKeyboardMarkup:
    select_group_button = InlineKeyboardButton(
        text="Поиск группы",
        switch_inline_query_current_chat="group:",
    )
    select_teacher_for_schedule = InlineKeyboardButton(
        text="Поиск расписания преподавателя",
        switch_inline_query_current_chat="teacher_schedule:",
    )
    select_teacher_button = InlineKeyboardButton(
        text="Рейтинг преподавателей",
        switch_inline_query_current_chat="teacher:",
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[select_group_button], [select_teacher_button], [select_teacher_for_schedule]]
    )
    return keyboard


def get_days_students_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="Понедельник", callback_data="day:MONDAY"),
            InlineKeyboardButton(text="Вторник", callback_data="day:TUESDAY")
        ],
        [
            InlineKeyboardButton(text="Среда", callback_data="day:WEDNESDAY"),
            InlineKeyboardButton(text="Четверг", callback_data="day:THURSDAY")
        ],
        [
            InlineKeyboardButton(text="Пятница", callback_data="day:FRIDAY"),
            InlineKeyboardButton(text="Суббота", callback_data="day:SATURDAY")
        ],
        [
            InlineKeyboardButton(text="Вернуться", callback_data="comeback")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_days_teacher_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="Понедельник", callback_data="teacher_day:MONDAY"),
            InlineKeyboardButton(text="Вторник", callback_data="teacher_day:TUESDAY")
        ],
        [
            InlineKeyboardButton(text="Среда", callback_data="teacher_day:WEDNESDAY"),
            InlineKeyboardButton(text="Четверг", callback_data="teacher_day:THURSDAY")
        ],
        [
            InlineKeyboardButton(text="Пятница", callback_data="teacher_day:FRIDAY"),
            InlineKeyboardButton(text="Суббота", callback_data="teacher_day:SATURDAY")
        ],
        [
            InlineKeyboardButton(text="Вернуться", callback_data="comeback")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def handle_group_search(query: str): # Ищем группу по первым буквам
    results = []
    if query:
        for key, value in groups.items():
            if query.lower() in key.lower() or query.lower() in value.lower():
                result_id = hashlib.md5(key.encode()).hexdigest()
                input_content = InputTextMessageContent(
                    message_text=f"Вы выбрали группу: {key} ({value})"
                )
                result = InlineQueryResultArticle(
                    id=result_id,
                    title=f"Группа: {key}",
                    input_message_content=input_content,
                    description=f"Код группы: {value}"
                )
                results.append(result)

    if query and not results:
        result_id = hashlib.md5(query.encode()).hexdigest()
        input_content = InputTextMessageContent(
            message_text="Группа не найдена. Пожалуйста, введите корректный код группы."
        )
        results.append(
            InlineQueryResultArticle(
                id=result_id,
                title="Группа не найдена",
                input_message_content=input_content,
                description="Нет такой группы."
            )
        )
    return results

async def handle_teacher_inline_search(query: str) -> list[InlineQueryResultArticle]: #Перехватываем поиск преподавателей и отдаем первые 50 совпадений
    results = []
    search = query.strip().lower()
    if not search:
        return results

    logger.info(f"Searching teachers for query: {search}")

    matched_teachers = await db.search_teachers(search)  

    for teacher in matched_teachers:
        name = teacher["full_name"]
        short_hash = teacher.get("hash") or hashlib.md5(name.encode()).hexdigest()
        avg, count = await db.get_teacher_rating(name)
        avg_str = f"{avg:.2f}"

        input_content = InputTextMessageContent(
            message_text=f"Преподаватель: {name}\n⭐ Рейтинг: {avg_str}/5\nКоличество оценок: {count}"
        )

        results.append(
            InlineQueryResultArticle(
                id=short_hash,
                title=name,
                input_message_content=input_content,
                description=f"Рейтинг: {avg_str}/5, оценок: {count}"
            )
        )

    # fallback, если ничего не найдено
    if not results:
        result_id = hashlib.md5(query.encode()).hexdigest()
        input_content = InputTextMessageContent(
            message_text="Преподаватель не найден. Пожалуйста, введите корректное имя."
        )
        results.append(
            InlineQueryResultArticle(
                id=result_id,
                title="Преподаватель не найден",
                input_message_content=input_content,
                description="Нет совпадений"
            )
        )

    return results


async def handle_teacher_inline_search_names(query: str) -> list[InlineQueryResultArticle]:
    results = []
    search = query.strip().lower()
    if not search:
        return results

    logger.info(f"Searching teachers (names only) for query: {search}")

    matched_teachers = await db.search_teachers(search)

    for teacher in matched_teachers:
        name = teacher["full_name"]
        short_hash = teacher.get("hash") or hashlib.md5(name.encode()).hexdigest()

        input_content = InputTextMessageContent(
            message_text=f"Преподаватель: {name}"
        )

        results.append(
            InlineQueryResultArticle(
                id=short_hash,
                title=name,  # в выдаче будет только ФИО
                input_message_content=input_content,
                description="Преподаватель"  # можно убрать или заменить
            )
        )

    # fallback, если ничего не найдено
    if not results:
        result_id = hashlib.md5(query.encode()).hexdigest()
        input_content = InputTextMessageContent(
            message_text="Преподаватель не найден. Пожалуйста, введите корректное имя."
        )
        results.append(
            InlineQueryResultArticle(
                id=result_id,
                title="Преподаватель не найден",
                input_message_content=input_content,
                description="Нет совпадений"
            )
        )

    return results




async def get_teacher_rating_keyboard(name: str) -> InlineKeyboardMarkup: 
    """
    Клавиатура для выбора рейтинга преподавателя от 0 до 5 звезд..
    """
    teachers = await db.search_teachers(name)
    if not teachers:
        # fallback, если нет такого преподавателя
        short_hash = hashlib.md5(name.encode()).hexdigest()
    else:
        teacher = teachers[0]  # берем первый результат
        short_hash = teacher.get("hash", hashlib.md5(name.encode()).hexdigest())

    buttons = []
    for i in range(6):  # 0,1,2,3,4,5 звезд
        stars = "⭐" * i if i > 0 else "0️⃣"
        buttons.append(InlineKeyboardButton(
            text=stars,
            callback_data=f"rate:{short_hash}:{i}"
        ))

    # Разбиваем на ряды по 3 кнопки
    keyboard = [buttons[i:i+3] for i in range(0, len(buttons), 3)]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_human_readable_schedule(data):
    days_map = {
        "MONDAY": "Понедельник",
        "TUESDAY": "Вторник",
        "WEDNESDAY": "Среда",
        "THURSDAY": "Четверг",
        "FRIDAY": "Пятница",
        "SATURDAY": "Суббота"
    }

    today = date.today()

    # Границы текущей недели
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)

    # Даты этой недели по ключу dayOfWeek
    week_day_dates = {
        "MONDAY": monday,
        "TUESDAY": monday + timedelta(days=1),
        "WEDNESDAY": monday + timedelta(days=2),
        "THURSDAY": monday + timedelta(days=3),
        "FRIDAY": monday + timedelta(days=4),
        "SATURDAY": monday + timedelta(days=5),
        "SUNDAY": monday + timedelta(days=6),
    }

    # Чётность недели
    week_type = "EVEN" if today.isocalendar().week % 2 == 0 else "ODD"

    schedule_by_day = {name: [] for name in days_map.values()}

    for item in data.get('data', {}).get('scheduleItems', []):
        day_key = item.get('dayOfWeek')
        day_ru = days_map.get(day_key)
        if not day_ru:
            continue

        # проверяем, что startDate в пределах текущей недели
        start_date_str = item.get('startDate')
        if not start_date_str:
            continue
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            continue

        if not (monday <= start_date <= sunday):
            continue

        lesson_date = week_day_dates.get(day_key)
        if not lesson_date:
            continue

        subject = item.get('subject', {})
        lesson = {
            "lessonNumber": item.get('lessonNumber'),
            "startTime": item.get('startTime'),
            "endTime": item.get('endTime'),
            "startDate": start_date_str,
            "date": lesson_date.isoformat(),
            "weekType": week_type,
            "subject": subject.get('name'),
            "subjectShort": subject.get('shortName'),
            "teachers": ", ".join(t.get('fullName') for t in item.get('teachers', []) if t.get('fullName')) or None,
            "classrooms": ", ".join(c.get('roomNumber') for c in item.get('classrooms', []) if c.get('roomNumber')) or None,
            "groups": ", ".join(g.get('name') for g in item.get('groups', []) if g.get('name')) or None
        }
        schedule_by_day[day_ru].append(lesson)

    # сортировка по времени
    for lessons in schedule_by_day.values():
        lessons.sort(key=lambda x: x['startTime'] or "")

    return schedule_by_day

def get_human_readable_teacher_schedule(data):
    days_map = {
        "MONDAY": "Понедельник",
        "TUESDAY": "Вторник",
        "WEDNESDAY": "Среда",
        "THURSDAY": "Четверг",
        "FRIDAY": "Пятница",
        "SATURDAY": "Суббота"
    }

    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)

    week_day_dates = {
        "MONDAY": monday,
        "TUESDAY": monday + timedelta(days=1),
        "WEDNESDAY": monday + timedelta(days=2),
        "THURSDAY": monday + timedelta(days=3),
        "FRIDAY": monday + timedelta(days=4),
        "SATURDAY": monday + timedelta(days=5),
        "SUNDAY": monday + timedelta(days=6),
    }

    week_type = "EVEN" if today.isocalendar().week % 2 == 0 else "ODD"

    schedule_by_day = {name: [] for name in days_map.values()}

    for item in data.get('data', {}).get('scheduleItems', []):
        day_key = item.get('dayOfWeek')
        day_ru = days_map.get(day_key)
        if not day_ru:
            continue

        start_date_str = item.get('startDate')
        if not start_date_str:
            continue
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            continue

        if not (monday <= start_date <= sunday):
            continue

        lesson_date = week_day_dates.get(day_key)
        subject = item.get('subject', {})

        lesson = {
            "lessonNumber": item.get('lessonNumber'),
            "startTime": item.get('startTime'),
            "endTime": item.get('endTime'),
            "startDate": start_date_str,
            "date": lesson_date.isoformat(),
            "weekType": week_type,
            "subject": subject.get('name'),
            "subjectShort": subject.get('shortName'),
            "groups": ", ".join(g.get('name') for g in item.get('groups', []) if g.get('name')) or None,
            "classrooms": ", ".join(c.get('roomNumber') for c in item.get('classrooms', []) if c.get('roomNumber')) or None
        }

        schedule_by_day[day_ru].append(lesson)

    for lessons in schedule_by_day.values():
        lessons.sort(key=lambda x: x['startTime'] or "")

    return schedule_by_day


def pretty_schedule_str(data: dict) -> str: # Тестовое форматирования для cli режима
    entity = data.get("data", {}).get("entity", {}) if isinstance(data, dict) else {}
    items = data.get("data", {}).get("scheduleItems", []) if isinstance(data, dict) else []
    order = {"MONDAY":0,"TUESDAY":1,"WEDNESDAY":2,"THURSDAY":3,"FRIDAY":4,"SATURDAY":5,"SUNDAY":6}
    ru = {"MONDAY":"Понедельник","TUESDAY":"Вторник","WEDNESDAY":"Среда",
          "THURSDAY":"Четверг","FRIDAY":"Пятница","SATURDAY":"Суббота","SUNDAY":"Воскресенье"}

    lines = []
    lines.append(f"{entity.get('facultyShort','')} — {entity.get('faculty','')}")
    lines.append(f"Группа: {entity.get('name','—')} | Курс: {entity.get('course','—')}")
    spec = entity.get('specialty') or {}
    lines.append(f"Специальность: {spec.get('code','—')} {spec.get('name','—')}")
    lines.append("="*80)

    by_day = defaultdict(list)
    for it in items:
        by_day[it.get("dayOfWeek","UNKNOWN")].append(it)

    for day in sorted(by_day.keys(), key=lambda k: order.get(k, 99)):
        lines.append(f"\n--- {ru.get(day, day)} ---")
        for it in sorted(by_day[day], key=lambda x: x.get("startTime","")):
            st = (it.get("startTime","")[:5] or "??:??")
            en = (it.get("endTime","")[:5] or "??:??")
            num = it.get("lessonNumber","-")
            subj = (it.get("subject") or {}).get("name","—")
            rooms = ", ".join(c.get("roomNumber","") for c in it.get("classrooms",[])) or "—"
            teachers = ", ".join(t.get("shortName","") for t in it.get("teachers",[])) or "—"
            groups = ", ".join(g.get("name","") for g in it.get("groups",[])) or "—"
            lines.append(f"{st}-{en} | №{num} | {subj} | Группы: {groups} | Каб.: {rooms} | Преп.: {teachers}")

    return "\n".join(lines)