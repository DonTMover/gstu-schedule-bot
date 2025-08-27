from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent
)
from loguru import logger  
from aiogram import types
from groupes import groups
import hashlib

days_map = {
    "MONDAY": "Понедельник",
    "TUESDAY": "Вторник",
    "WEDNESDAY": "Среда",
    "THURSDAY": "Четверг",
    "FRIDAY": "Пятница",
    "SATURDAY": "Суббота"
}

# Старое - скоро удалю
# def get_inline_keyboard_select_group() -> InlineKeyboardMarkup:
#     select_button = InlineKeyboardButton(
#         text="Поиск",
#         switch_inline_query_current_chat="",
#     )
#     keyboard = InlineKeyboardMarkup(inline_keyboard=[[select_button]])
#     return keyboard

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


# --- Обработчик поиска преподавателей ---
def handle_teacher_search(query: str):
    results = []
    # TMP TODO
    teachers = {
        "иванов": "Иванов И.И. — ⭐⭐⭐⭐☆",
        "петров": "Петров П.П. — ⭐⭐⭐⭐⭐",
    }

    if query:
        for name, rating in teachers.items():
            if query.lower() in name.lower():
                result_id = hashlib.md5(name.encode()).hexdigest()
                input_content = InputTextMessageContent(
                    message_text=f"Преподаватель: {rating}"
                )
                result = InlineQueryResultArticle(
                    id=result_id,
                    title=f"Преподаватель: {name.title()}",
                    input_message_content=input_content,
                    description=rating
                )
                results.append(result)

    if query and not results:
        result_id = hashlib.md5(query.encode()).hexdigest()
        input_content = InputTextMessageContent(
            message_text="Преподаватель не найден."
        )
        results.append(
            InlineQueryResultArticle(
                id=result_id,
                title="Преподаватель не найден",
                input_message_content=input_content,
                description="Нет такого преподавателя."
            )
        )
    return results

