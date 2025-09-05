from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    InlineQueryResultArticle, InputTextMessageContent
)
from loguru import logger
from datetime import datetime, date, timedelta
from collections import defaultdict
import hashlib

from db import db
from groupes import groups

# ======================= Константы =======================
DAYS_MAP = {
    "MONDAY": "Понедельник",
    "TUESDAY": "Вторник",
    "WEDNESDAY": "Среда",
    "THURSDAY": "Четверг",
    "FRIDAY": "Пятница",
    "SATURDAY": "Суббота",
    "SUNDAY": "Воскресенье"
}

# =================== Inline-клавиатуры ===================
def get_inline_keyboard_disclaimer() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Принять", callback_data="disclaimer:accept")]]
    )

def get_inline_keyboard_select() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Поиск группы", switch_inline_query_current_chat="group:")],
            [InlineKeyboardButton(text="Рейтинг преподавателей", switch_inline_query_current_chat="teacher:")],
            [InlineKeyboardButton(text="Поиск расписания преподавателя", switch_inline_query_current_chat="teacher_schedule:")]
        ]
    )

def get_days_keyboard(for_teacher=False) -> InlineKeyboardMarkup:
    prefix = "teacher_day:" if for_teacher else "day:"
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
        InlineKeyboardButton(text=("⭐" * i if i > 0 else "0️⃣"), callback_data=f"rate:{short_hash}:{i}")
        for i in range(6)
    ]
    # Разбиваем по 3 кнопки в ряд
    keyboard = [buttons[i:i+3] for i in range(0, len(buttons), 3)]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# =================== Поиск ===================
def handle_group_search(query: str):
    results = []
    if query:
        for key, value in groups.items():
            if query.lower() in key.lower() or query.lower() in value.lower():
                result_id = hashlib.md5(key.encode()).hexdigest()
                results.append(
                    InlineQueryResultArticle(
                        id=result_id,
                        title=f"Группа: {key}",
                        input_message_content=InputTextMessageContent(message_text=f"Вы выбрали группу: {key} ({value})"),
                        description=f"Код группы: {value}"
                    )
                )
    if query and not results:
        result_id = hashlib.md5(query.encode()).hexdigest()
        results.append(
            InlineQueryResultArticle(
                id=result_id,
                title="Группа не найдена",
                input_message_content=InputTextMessageContent(message_text="Группа не найдена. Пожалуйста, введите корректный код группы."),
                description="Нет такой группы."
            )
        )
    return results

async def handle_teacher_inline_search(query: str, names_only=False):
    results = []
    search = query.strip().lower()
    if not search:
        return results

    logger.info(f"Searching teachers for query: {search}")
    matched_teachers = await db.search_teachers(search)

    for teacher in matched_teachers:
        name = teacher["full_name"]
        short_hash = teacher.get("hash") or hashlib.md5(name.encode()).hexdigest()
        if names_only:
            input_content = InputTextMessageContent(message_text=f"Преподаватель: {name}")
            description = "Преподаватель"
        else:
            avg, count = await db.get_teacher_rating(name)
            avg_str = f"{avg:.2f}"
            input_content = InputTextMessageContent(
                message_text=f"Преподаватель: {name}\n⭐ Рейтинг: {avg_str}/5\nКоличество оценок: {count}"
            )
            description = f"Рейтинг: {avg_str}/5, оценок: {count}"

        results.append(
            InlineQueryResultArticle(
                id=short_hash,
                title=name,
                input_message_content=input_content,
                description=description
            )
        )

    if not results:
        result_id = hashlib.md5(query.encode()).hexdigest()
        results.append(
            InlineQueryResultArticle(
                id=result_id,
                title="Преподаватель не найден",
                input_message_content=InputTextMessageContent(message_text="Преподаватель не найден. Пожалуйста, введите корректное имя."),
                description="Нет совпадений"
            )
        )
    return results

# =================== Расписание ===================
def get_human_readable_schedule_generic(data, for_teacher=False):
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    week_type = "EVEN" if today.isocalendar().week % 2 == 0 else "ODD"

    schedule_by_day = {name: [] for name in DAYS_MAP.values()}
    week_day_dates = {k: monday + timedelta(days=i) for i, k in enumerate(DAYS_MAP)}

    for item in data.get('data', {}).get('scheduleItems', []):
        day_key = item.get('dayOfWeek')
        day_ru = DAYS_MAP.get(day_key)
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

        subject = item.get('subject', {})
        lesson = {
            "lessonNumber": item.get('lessonNumber'),
            "startTime": item.get('startTime'),
            "endTime": item.get('endTime'),
            "startDate": start_date_str,
            "date": week_day_dates.get(day_key).isoformat(),
            "weekType": week_type,
            "subject": subject.get('name'),
            "subjectShort": subject.get('shortName'),
            "groups": ", ".join(g.get('name') for g in item.get('groups', []) if g.get('name')) or None
        }

        if not for_teacher:
            lesson["teachers"] = ", ".join(t.get('fullName') for t in item.get('teachers', []) if t.get('fullName')) or None
            lesson["classrooms"] = ", ".join(c.get('roomNumber') for c in item.get('classrooms', []) if c.get('roomNumber')) or None

        schedule_by_day[day_ru].append(lesson)

    for lessons in schedule_by_day.values():
        lessons.sort(key=lambda x: x['startTime'] or "")
    return schedule_by_day

def get_human_readable_schedule(data):
    return get_human_readable_schedule_generic(data, for_teacher=False)

def get_human_readable_teacher_schedule(data):
    return get_human_readable_schedule_generic(data, for_teacher=True)

# =================== CLI форматирование ===================
def pretty_schedule_str(data: dict) -> str:
    entity = data.get("data", {}).get("entity", {}) if isinstance(data, dict) else {}
    items = data.get("data", {}).get("scheduleItems", []) if isinstance(data, dict) else []
    order = {k: i for i, k in enumerate(DAYS_MAP)}
    lines = [
        f"{entity.get('facultyShort','')} — {entity.get('faculty','')}",
        f"Группа: {entity.get('name','—')} | Курс: {entity.get('course','—')}"
    ]
    spec = entity.get('specialty') or {}
    lines.append(f"Специальность: {spec.get('code','—')} {spec.get('name','—')}")
    lines.append("="*80)

    by_day = defaultdict(list)
    for it in items:
        by_day[it.get("dayOfWeek","UNKNOWN")].append(it)

    for day in sorted(by_day.keys(), key=lambda k: order.get(k, 99)):
        lines.append(f"\n--- {DAYS_MAP.get(day, day)} ---")
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