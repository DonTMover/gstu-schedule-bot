from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
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

def get_inline_keyboard_select_group() -> InlineKeyboardMarkup:
    select_button = InlineKeyboardButton(
        text="Поиск",
        switch_inline_query_current_chat="",
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[select_button]])
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
