from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent
)
from loguru import logger  
from aiogram import types
from groupes import groups
import hashlib

from db import db

days_map = {
    "MONDAY": "Понедельник",
    "TUESDAY": "Вторник",
    "WEDNESDAY": "Среда",
    "THURSDAY": "Четверг",
    "FRIDAY": "Пятница",
    "SATURDAY": "Суббота"
}


def get_inline_keyboard_select() -> InlineKeyboardMarkup:
    select_group_button = InlineKeyboardButton(
        text="Поиск группы",
        switch_inline_query_current_chat="group:",
    )
    select_teacher_button = InlineKeyboardButton(
        text="Рейтинг преподавателей",
        switch_inline_query_current_chat="teacher:",
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[select_group_button], [select_teacher_button]]
    )
    return keyboard


def get_days_keyboard() -> InlineKeyboardMarkup:
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
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def handle_group_search(query: str):
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

def handle_teacher_inline_search(query: str) -> list[InlineQueryResultArticle]:
    results = []

    search = query.strip().lower()
    if not search:
        return results
    
    print("IN UTILS")
    logger.info("IN UTILS")

    # Найдём совпадения в базе преподавателей
    matched = [name for name in db.teachers.keys() if search in name.lower()]

    for name in matched[:50]:  # ограничиваем 50 результатами
        avg, count = db.get_teacher_rating(name)
        avg_str = f"{avg:.2f}"  # среднее с 2 знаками после запятой
        result_id = hashlib.md5(name.encode()).hexdigest()
        input_content = InputTextMessageContent(
            message_text=f"Преподаватель: {name}\n⭐ Рейтинг: {avg_str}/5\nКоличество оценок: {count}"
        )

        results.append(
            InlineQueryResultArticle(
                id=result_id,
                title=name,
                input_message_content=input_content,
                description=f"Рейтинг: {avg_str}/5, оценок: {count}"
            )
        )

    return results


# Получаем клавиатуру для оценки преподавателя
def get_teacher_rating_keyboard(name: str) -> InlineKeyboardMarkup:
    """
    Клавиатура для выбора рейтинга преподавателя от 0 до 5 звезд
    """
    buttons = []
    for i in range(6):  # 0,1,2,3,4,5
        stars = "⭐" * i if i > 0 else "0️⃣"
        buttons.append(InlineKeyboardButton(
            text=stars,
            callback_data=f"rate:{name}:{i}"
        ))

    # Разбиваем на ряды по 3 кнопки
    keyboard = [buttons[i:i+3] for i in range(0, len(buttons), 3)]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
