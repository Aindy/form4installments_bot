from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardButton, InlineKeyboardMarkup)
from bot import categories


def get_category_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [InlineKeyboardButton(text=category, callback_data=f"category_{category}") for category in categories]
    keyboard.add(*buttons)
    return keyboard

# def get_category_keyboard():
#     keyboard = InlineKeyboardMarkup(row_width=1)
#     button = InlineKeyboardButton(
#         text="Тестовая категория",
#         callback_data=f"category_test")
#     keyboard.add(button)

#     return keyboard


def get_link_to_subscribe(link):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(InlineKeyboardButton(text='Подписаться',url=link))
    return keyboard

# def get_keyboard() -> ReplyKeyboardMarkup:
#     kb = ReplyKeyboardMarkup(resize_keyboard=True)
#     kb.add(
#         KeyboardButton('Создать заявку'),
#         KeyboardButton('Помощь'),
#     )

#     return kb


# def get_kb_moder() -> ReplyKeyboardMarkup:
#     kb = ReplyKeyboardMarkup(resize_keyboard=True)
#     kb.add(
#         KeyboardButton('Обновить')
#     )

#     return kb


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        KeyboardButton('Отмена'),
    )

    return kb


# def get_done_keyboard() -> ReplyKeyboardMarkup:
#     kb = ReplyKeyboardMarkup(resize_keyboard=True)
#     kb.add(
#         KeyboardButton('Готово'),
#     )

#     return kb


def get_inline_keyboard(user_id) -> InlineKeyboardMarkup:
    approve_button = InlineKeyboardButton(
        text="Одобрить",
        callback_data=f"approve:{user_id}"
        )
    reject_button = InlineKeyboardButton(
        text="Отклонить",
        callback_data=f"reject:{user_id}"
        )
    keyboard = InlineKeyboardMarkup().add(approve_button, reject_button)

    return keyboard



# def get_pay_kb(user_id) -> InlineKeyboardMarkup:
#     keyboard = InlineKeyboardMarkup(row_width=3)
#     button_1 = InlineKeyboardButton(
#         text="1 месяц",
#         callback_data=f"subscribe_Месяц:{user_id}")
#     button_2 = InlineKeyboardButton(
#         text="3 месяца",
#         callback_data=f"subscribe_Квартал:{user_id}")
#     button_3 = InlineKeyboardButton(
#         text="1 год",
#         callback_data=f"subscribe_Год:{user_id}")

#     keyboard.add(button_1, button_2, button_3)

#     return keyboard
