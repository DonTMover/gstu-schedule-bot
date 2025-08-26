from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from loguru import logger  
from aiogram import types
from groupes import groups
import hashlib

def get_inline_keyboard_select_group() -> InlineKeyboardMarkup:
    select_button = InlineKeyboardButton(
        text="Поиск",
        switch_inline_query_current_chat="",
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[select_button]])
    return keyboard



def get_inline_keyboard() -> InlineKeyboardMarkup:
    button1 = InlineKeyboardButton(text="Button 1", callback_data="button1")
    button2 = InlineKeyboardButton(text="Button 2", callback_data="button2")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button1, button2]])
    return keyboard

