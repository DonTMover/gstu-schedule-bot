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

def get_subgroup_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Подгруппа 1", callback_data="subgroup:1"),
            InlineKeyboardButton(text="Подгруппа 2", callback_data="subgroup:2"),
            InlineKeyboardButton(text="Без подгруппы", callback_data="subgroup:0")
        ]
    ])


def get_days_keyboard(for_teacher=False) -> InlineKeyboardMarkup:
    prefix = "teacher_day:" if for_teacher else "day:"
    buttons = [
        [
            InlineKeyboardButton(text="Понедельник", callback_data=f"{prefix}MONDAY"),
            InlineKeyboardButton(text="Вторник", callback_data=f"{prefix}TUESDAY")
        ],
        [
            InlineKeyboardButton(text="Среда", callback_data=f"{prefix}WEDNESDAY"),
            InlineKeyboardButton(text="Четверг", callback_data=f"{prefix}THURSDAY")
        ],
        [
            InlineKeyboardButton(text="Пятница", callback_data=f"{prefix}FRIDAY"),
            InlineKeyboardButton(text="Суббота", callback_data=f"{prefix}SATURDAY")
        ],
        [
            InlineKeyboardButton(text="Прошлая неделя <--", callback_data="week:prev"),
            InlineKeyboardButton(text="Следующая неделя -->", callback_data="week:next")
        ],
        [
            InlineKeyboardButton(text="Вернуться", callback_data="comeback")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


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
def get_human_readable_schedule_generic(data, for_teacher=False, monday: date = None):
    # Если monday не передан — используем текущую неделю
    if monday is None:
        today = date.today()
        monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    week_type = "EVEN" if monday.isocalendar().week % 2 == 0 else "ODD"

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

        # Теперь фильтруем по переданной неделе
        if not (monday <= start_date <= sunday):
            continue

        # Фильтрация по weekType
        item_week_type = item.get('weekType', 'ALL')
        # Если ALL или None — показываем всегда
        if item_week_type in ('ALL', None):
            pass
        # Если ODD/EVEN — сравниваем с текущей неделей
        elif item_week_type in ('ODD', 'EVEN'):
            if item_week_type != week_type:
                continue
        # Если что-то другое — пропускаем
        else:
            continue

        subject = item.get('subject', {})
        lesson_type = item.get('lessonType') or {}
        lesson = {
            "lessonNumber": item.get('lessonNumber'),
            "startTime": item.get('startTime'),
            "endTime": item.get('endTime'),
            "startDate": start_date_str,
            "date": week_day_dates.get(day_key).isoformat(),
            "weekType": week_type,
            "subject": subject.get('name'),
            "subjectShort": subject.get('shortName'),
            "lessonType": lesson_type.get('name'),
            "lessonTypeShort": lesson_type.get('shortName'),
            "groups": ", ".join(g.get('name') for g in item.get('groups', []) if g.get('name')) or None
        }

        if not for_teacher:
            lesson["teachers"] = ", ".join(t.get('fullName') for t in item.get('teachers', []) if t.get('fullName')) or None
            lesson["classrooms"] = ", ".join(c.get('roomNumber') for c in item.get('classrooms', []) if c.get('roomNumber')) or None

        schedule_by_day[day_ru].append(lesson)

    for lessons in schedule_by_day.values():
        lessons.sort(key=lambda x: x['startTime'] or "")
    return schedule_by_day

def get_human_readable_schedule(data, monday: date = None):
    return get_human_readable_schedule_generic(data, for_teacher=False, monday=monday)

def get_human_readable_teacher_schedule(data, monday: date = None):
    return get_human_readable_schedule_generic(data, for_teacher=True, monday=monday)

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