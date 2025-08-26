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

@dp.callback_query(lambda c: c.data == "search")
async def process_search(callback_query):
    await callback_query.message.answer("Please enter the group code (e.g., АП-11):")
    await callback_query.answer()


def get_inline_keyboard() -> InlineKeyboardMarkup:
    button1 = InlineKeyboardButton(text="Button 1", callback_data="button1")
    button2 = InlineKeyboardButton(text="Button 2", callback_data="button2")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button1, button2]])
    return keyboard

@dp.callback_query(lambda c: c.data == "button1")
async def process_button1(callback_query):
    await callback_query.message.answer("You clicked Button 1!")
    await callback_query.answer()
    
@dp.callback_query(lambda c: c.data == "button2")
async def process_button2(callback_query):
    await callback_query.message.answer("You clicked Button 2!")
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