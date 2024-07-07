from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from aiogram.types import  InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.dispatcher.filters import BoundFilter, Text
from aiogram.types import ChatActions
from datetime import datetime, timedelta
from dotenv import load_dotenv
import asyncio
import logging
import ast
import sys
import re
from os import getenv

import async_sqlite as sq
import keyboards as kb


load_dotenv()

# PROXY_URL для обхода блокировок на PythonEveryWhere
# PROXY_URL = "http://proxy.server:3128"

TOKEN = getenv("BOT_TOKEN")
ADMIN_GROUP = getenv("ADMIN_GROUP")
APPROVE_GROUP = getenv("APPROVE_GROUP")
# ADMIN_GROUP = ADMIN_GROUP.split(",") if ADMIN_GROUP else []
SUB_GROUP = getenv("SUB_GROUP", "")
# ADMIN_GROUP = ADMIN_GROUP.split(",") if ADMIN_GROUP else []
LINK_TO_GROUP = 'https://web.telegram.org/k/#-2233720705'
phone_number_pattern = re.compile(r'^\+?[1-9]\d{1,14}$')

bot = Bot(TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
categories = [
    "Телефоны", "Часы", "Колеса", "Автодиски", "Сантехника",
    "Посуда", "Ламинат", "Окна", "Двери", "Стройматериалы",
    "Телевизоры", "Автозапчасти", "Бытовая техника", "Мебель",
    "Люстры", "Кондиционеры"
]


async def on_startup(_):
    await sq.db_start()


class Form(StatesGroup):
    name = State()  # Ожидание ввода имени
    surname = State()  # Ожидание ввода фамилии
    middle_name = State()  # Ожидание ввода отчества (если есть)
    city_of_registration = State()  # Ожидание ввода города прописки
    city_of_residence = State()  # Ожидание ввода города проживания
    phone_number = State()  # Ожидание ввода номера телефона
    passport_scans = State()  # Ожидание загрузки сканов паспорта
    selfie_with_passport = State()  # Ожидание загрузки селфи с паспортом
    monthly_income = State()  # Ожидание ввода дохода в месяц
    employment_status = State()  # Ожидание ввода статуса работы
    organization_number = State()  # Ожидание ввода номера организации
    guarantor_info = State()  # Ожидание ввода данных поручителя
    guarantor_passport = State()  # Ожидание загрузки пасспорта поручителя
    category_choice = State()  # Ожидание выбора категории товара
    product_choice = State()  # Ожидание ввода товара и цены
    cost_product = State()  # Ожидание ввода цены товара
    installment_terms = State()  # Ожидание выбора условий рассрочки


@dp.message_handler(commands='get_chat_id')
async def get_chat_id(message: types.Message):
    chat_id = message.chat.id
    await message.answer(f"Chat ID: {chat_id}")


class IsSubscriber(BoundFilter):
    async def check(self, message: types.Message):
        try:
            # Получаем id чата из публичного никнейма
            # chat = await bot.get_chat(SUB_GROUP)
            # chat_id = chat.id

            # Проверяем статус подписки
            sub = await bot.get_chat_member(chat_id=SUB_GROUP, user_id=message.from_user.id)
            if sub.status == types.ChatMemberStatus.LEFT:
                await bot.send_message(
                    chat_id=message.from_user.id,
                    text='Подпишитесь на телеграм группу и повторите попытку',
                    reply_markup=kb.get_link_to_subscribe(LINK_TO_GROUP)
                )
                return False
        except Exception as e:
            logging.error(f"Ошибка при проверке подписки в группе {SUB_GROUP}: {e}")
            await bot.send_message(
                chat_id=message.from_user.id,
                text=f"Не удалось проверить подписку в группе {LINK_TO_GROUP}. Попробуйте позже."
            )
            return False
        return True

dp.filters_factory.bind(IsSubscriber)


# Создание пользовательского фильтра для типа чата
class ChatTypeFilter(BoundFilter):
    key = 'chat_type'

    def __init__(self, chat_type):
        if not isinstance(chat_type, list):
            chat_type = [chat_type]
        self.chat_type = chat_type

    async def check(self, message: types.Message) -> bool:
        return message.chat.type in self.chat_type

# Регистрация фильтра
dp.filters_factory.bind(ChatTypeFilter)


@dp.message_handler(Text(equals="Отмена"), state='*', chat_type=types.ChatType.PRIVATE)
async def save_contact_handler(message: types.Message, state: FSMContext) -> None:
    """
    Отменяет процесс заполнения заявки
    """
    await state.finish()
    await message.reply(text='Вы отменили заявку.\nЧтобы начать заново нажмите /ready',
                        reply_markup=types.ReplyKeyboardRemove())


# Стартовое сообщение
@dp.message_handler(commands='start', chat_type=types.ChatType.PRIVATE)
async def send_welcome(message: types.Message):
    await message.bot.send_chat_action(message.chat.id, ChatActions.TYPING)
    await asyncio.sleep(1)
    await message.reply(text='Добро пожаловать!\nЧтобы пользоваться данным ботом Вам необходимо подписаться на нашу группу.\n'
                        'После этого для оформления заявки на рассрочку нажмите /ready',
                        reply_markup=kb.get_link_to_subscribe(LINK_TO_GROUP))


@dp.message_handler(IsSubscriber(), commands='ready', chat_type=types.ChatType.PRIVATE)
async def apply_for_installment(message: types.Message):
    await sq.create_profile(user_id=message.from_user.id)
    await message.bot.send_chat_action(message.chat.id, ChatActions.TYPING)
    await asyncio.sleep(1)
    user_data = await sq.get_status(message.from_user.id)

    if user_data:
        status_check = user_data[18]
        timestamp = user_data[20]

        if status_check == 2:
            status_check_time = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            if datetime.now() - status_check_time > timedelta(days=30):
                # Сброс status_check до 0, если прошло больше месяца
                await sq.update_profile({'status_check': 0}, message.from_user.id)
                status_check = 0
            else:
                await message.reply("Вашу заявку уже отклонили, пожалуйста обратитесь позже.")
        elif status_check == 1:
            await message.reply(f'У вас уже есть одобренная рассрочка.\n\n'
                                f'Товар: {user_data[14]}, {user_data[15]}\n'
                                f'{user_data[17]}')
            await message.answer(f'Если хотите сформировать заявку заново нажмите /reset')
        else:
            await message.bot.send_chat_action(message.chat.id, ChatActions.TYPING)
            await Form.name.set()
            await asyncio.sleep(1)
            await message.reply(text="Пожалуйста, введите ваше имя:",
                                reply_markup=kb.get_cancel_keyboard())


@dp.message_handler(IsSubscriber(), commands='reset', chat_type=types.ChatType.PRIVATE)
async def apply_for_installment(message: types.Message):
    await sq.create_profile(user_id=message.from_user.id)
    await message.bot.send_chat_action(message.chat.id, ChatActions.TYPING)
    await asyncio.sleep(1)
    user_data = await sq.get_status(message.from_user.id)
    if user_data:
        status_check = user_data[18]
        if status_check == 2:
            await message.reply("Вашу заявку уже отклонили, пожалуйста обратитесь позже.")
        if status_check == 1:
            await message.bot.send_chat_action(message.chat.id, ChatActions.TYPING)
            await Form.name.set()
            await asyncio.sleep(1)
            await message.reply(text="Пожалуйста, введите ваше имя:",
                                reply_markup=kb.get_cancel_keyboard())


# Получаем имя пользователя и переходим к следующему состоянию
@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await Form.next()
    await message.bot.send_chat_action(message.chat.id, ChatActions.TYPING)
    await asyncio.sleep(1)
    await message.reply("Введите вашу фамилию:")


# Получаем фамилию пользователя и переходим к следующему состоянию
@dp.message_handler(state=Form.surname)
async def process_surname(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['surname'] = message.text
    await Form.next()
    await message.bot.send_chat_action(message.chat.id, ChatActions.TYPING)
    await asyncio.sleep(1)
    await message.reply("Введите ваше отчество (если есть):")


# Получаем отчество пользователя и переходим к следующему состоянию
@dp.message_handler(state=Form.middle_name)
async def process_middle_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['middle_name'] = message.text
    await Form.next()
    await message.bot.send_chat_action(message.chat.id, ChatActions.TYPING)
    await asyncio.sleep(1)
    await message.reply("Введите ваш город прописки:")


# Получаем город прописки пользователя и переходим к следующему состоянию
@dp.message_handler(state=Form.city_of_registration)
async def process_city_of_registration(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['city_of_registration'] = message.text
    await Form.next()
    await message.bot.send_chat_action(message.chat.id, ChatActions.TYPING)
    await asyncio.sleep(1)
    await message.reply("Введите ваш город проживания:")


# Получаем город проживания пользователя и переходим к следующему состоянию
@dp.message_handler(state=Form.city_of_residence)
async def process_city_of_residence(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['city_of_residence'] = message.text
    await Form.next()
    await message.bot.send_chat_action(message.chat.id, ChatActions.TYPING)
    await asyncio.sleep(1)
    await request_phone(message)


@dp.message_handler(state=Form.phone_number)
async def request_phone(message: types.Message) -> None:
    """
    Запрашивает номер телефона от пользователя
    """
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                   one_time_keyboard=True)
    btn = types.KeyboardButton(text='Отправить номер телефона',
                               request_contact=True)
    kb.add(btn)
    await message.bot.send_chat_action(message.chat.id, ChatActions.TYPING)
    await asyncio.sleep(1)
    await message.answer(
        'Отправьте номер телефона по кнопке ниже.',
        reply_markup=kb
        )


@dp.message_handler(content_types=['contact'], state=Form.phone_number)
async def save_contact_handler(message: types.Message, state: FSMContext) -> None:
    """
    Принимает контакт в состоянии приемки номера,
    проверяет номер по рег выражению
    """
    if phone_number_pattern.match(message.contact.phone_number):
        await message.bot.send_chat_action(message.chat.id, ChatActions.TYPING)
        await asyncio.sleep(1)

        await message.answer(
            text='Номер телефона принят.\n',
            reply_markup=types.ReplyKeyboardRemove()
        )

        async with state.proxy() as data:
            data['phone_number'] = message.contact.phone_number
            data['passport_scans'] = []
        await Form.next()
        await message.bot.send_chat_action(message.chat.id, ChatActions.TYPING)
        await asyncio.sleep(1)
        await message.reply(text="Загрузите сканы паспорта (обе стороны с фото и пропиской.\nОтправьте поочередно, максимум 2 фотографии:):",
                            reply_markup=kb.get_cancel_keyboard())




# Получаем сканы паспорта поручителя и переходим к следующему состоянию после получения двух фотографий
@dp.message_handler(content_types=['photo'], state=Form.passport_scans)
async def process_guarantor_passport_scans(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['passport_scans'].append(message.photo[-1].file_id)
        if len(data['passport_scans']) < 2:
            await message.reply("Загрузите еще одну фотографию паспорта:")
        else:
            await Form.next()
            await message.bot.send_chat_action(message.chat.id, ChatActions.TYPING)
            await asyncio.sleep(1)
            await message.reply("Загрузите селфи с паспортом:")


# Получаем селфи с паспортом пользователя и переходим к следующему состоянию
@dp.message_handler(content_types=['photo'], state=Form.selfie_with_passport)
async def process_selfie_with_passport(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['selfie_with_passport'] = message.photo[-1].file_id
    await Form.next()
    await message.bot.send_chat_action(message.chat.id, ChatActions.TYPING)
    await asyncio.sleep(1)
    await message.reply("Введите ваш доход в месяц:")


@dp.message_handler(
    lambda message: not message.photo or message.document,
    state=[Form.passport_scans, Form.selfie_with_passport, Form.guarantor_passport])
async def check_type_photo_message(message: types.Message):
    """
    Проверяет сообщения на факт содеражания фотографии
    """
    await message.reply('Кажется вы прислали не фото..')


# Получаем доход пользователя и переходим к следующему состоянию
@dp.message_handler(state=Form.monthly_income)
async def process_monthly_income(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['monthly_income'] = message.text
    await Form.next()
    await message.bot.send_chat_action(message.chat.id, ChatActions.TYPING)
    await asyncio.sleep(1)
    await message.reply("Вы официально работаете? (да/нет):")


# Получаем статус работы пользователя и переходим к следующему состоянию
@dp.message_handler(state=Form.employment_status)
async def process_employment_status(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['employment_status'] = message.text
    await Form.next()
    await message.bot.send_chat_action(message.chat.id, ChatActions.TYPING)
    await asyncio.sleep(1)
    await message.reply("Введите номер организации:")


# Получаем номер организации пользователя и переходим к следующему состоянию
@dp.message_handler(state=Form.organization_number)
async def process_organization_number(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['organization_number'] = message.text
    await Form.next()
    await message.bot.send_chat_action(message.chat.id, ChatActions.TYPING)
    await asyncio.sleep(1)
    await message.reply("Введите данные поручителя (ФИО, номер телефона):")


# Получаем данные поручителя и переходим к следующему состоянию
@dp.message_handler(state=Form.guarantor_info)
async def process_guarantor_info(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['guarantor_info'] = message.text
        data['guarantor_passport'] = []  # Инициализируем список для фотографий
    await Form.next()
    await message.bot.send_chat_action(message.chat.id, ChatActions.TYPING)
    await asyncio.sleep(1)
    await message.reply("Прикрепите фото/скан паспорта обеих сторон (главная/прописка) поручителя.\nОтправьте поочередно, максимум 2 фотографии:")


# Получаем сканы паспорта поручителя и переходим к следующему состоянию после получения двух фотографий
@dp.message_handler(content_types=['photo'], state=Form.guarantor_passport)
async def process_guarantor_passport_scans(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['guarantor_passport'].append(message.photo[-1].file_id)
        if len(data['guarantor_passport']) < 2:
            await message.reply("Загрузите еще одну фотографию паспорта:")
        else:
            await Form.next()
            await message.reply("Выберите категорию товара:", reply_markup=kb.get_category_keyboard())


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('category_'), state=Form.category_choice)
async def process_category_choice(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        category = callback_query.data.split('_')[1]
        await callback_query.answer(f'Категория {category}')
        async with state.proxy() as data:
            data['category_choice'] = category
        await Form.next()
        await bot.send_message(callback_query.from_user.id, f"Вы выбрали категорию: {category}\nВведите название и модель товара:")
        await bot.answer_callback_query(callback_query.id)
    except Exception as e:
        logging.error(f'Ошибка в process_category_choice: {e}')


@dp.message_handler(state=Form.product_choice)
async def process_product_choice(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['product_choice'] = message.text
    await Form.next()
    await message.reply("Введите цену товара:")


@dp.message_handler(lambda message: not message.text.isdigit() or not (8000 <= int(message.text) <= 500000), state=Form.cost_product)
async def process_invalid_price(message: types.Message):
    await message.reply("Некорректная цена. Введите цену в диапазоне от 8 000 до 500 000 рублей:")


@dp.message_handler(lambda message: message.text.isdigit() and 8000 <= int(message.text) <= 500000, state=Form.cost_product)
async def process_price(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['cost_product'] = int(message.text)
    await Form.next()
    await message.bot.send_chat_action(message.chat.id, ChatActions.TYPING)
    await asyncio.sleep(2)
    await message.reply("Подождите немного, мы считаем…")
    await asyncio.sleep(5)
    await show_installment_options(message, state)
    

async def show_installment_options(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        price = data['cost_product']
        initial_payment = price * 0.3
        markup = InlineKeyboardMarkup(row_width=1)
        options = []

        for months in range(3, 13):
            if months == 12 and price <= 100000:
                continue
            monthly_payment = ((price - initial_payment) * (1 + 0.05 * months)) / months
            options.append(InlineKeyboardButton(f"{months} мес: {monthly_payment:.2f} руб/мес", callback_data=f"months_{months}"))

        markup.add(*options)
        markup.add(InlineKeyboardButton("Отмена", callback_data="cancel"))
        await message.reply(
            f"Цена товара: {price} руб.\nПервоначальный взнос (30%): {initial_payment:.2f} руб.\nВыберите срок рассрочки:",
            reply_markup=markup
        )

@dp.callback_query_handler(lambda c: c.data.startswith('months_'), state=Form.installment_terms)
async def process_installment_choice(callback_query: types.CallbackQuery, state: FSMContext):
    months = int(callback_query.data.split('_')[1])
    await callback_query.answer(f'Рассрочка на  {months} мес')
    async with state.proxy() as data:
        price = data['cost_product']
        initial_payment = price * 0.3
        monthly_payment = ((price - initial_payment) * (1 + 0.05 * months)) / months
        data['installment_choice'] = {
            "months": months,
            "monthly_payment": monthly_payment,
            "initial_payment": initial_payment
        }
        data['installment_terms'] = f"На {months} месяцев.\nЕжемесячный платеж: {monthly_payment:.2f} руб.\nПервоначальный взнос: {initial_payment:.2f} руб."
        data['status_check'] = 0
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Да, я согласен", callback_data="confirm"))
    markup.add(InlineKeyboardButton("Отмена", callback_data="cancel"))

    await bot.send_message(
        callback_query.from_user.id,
        f"Вы выбрали рассрочку на {months} месяцев.\nЕжемесячный платеж: {monthly_payment:.2f} руб.\nПервоначальный взнос: {initial_payment:.2f} руб.\nПодтверждаете?",
        reply_markup=markup
    )



@dp.callback_query_handler(lambda c: c.data == 'confirm', state=Form.installment_terms)
async def process_confirm(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer(f'Готово')
    data = await state.get_data()
    await sq.update_profile(data, callback_query.from_user.id)
    await send_profile_to_moderation(data, ADMIN_GROUP, callback_query.bot, callback_query.from_user.id)
    await callback_query.message.answer(text="Ваша заявка отправлена на рассмотрение.",
                                        reply_markup=types.ReplyKeyboardRemove())
    await state.finish()


@dp.callback_query_handler(lambda c: c.data == 'cancel', state=Form.installment_terms)
async def process_cancel(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer(f'Отмена заявки')
    await state.finish()
    await bot.send_message(callback_query.from_user.id, "Заявка отменена.")
    await bot.answer_callback_query(callback_query.id)


async def send_profile_to_moderation(profile, ADMIN_GROUP, bot, user_id) -> None:
    """
    Отправляет профиль пользователя на модерацию.
    """
    user_tg = f"tg://user?id={user_id}"
    name = profile['name']
    surname = profile['surname']
    middle_name = profile['middle_name']
    city_of_registration = profile['city_of_registration']
    city_of_residence = profile['city_of_residence']
    phone_number = profile['phone_number']
    passport_scans = profile['passport_scans']
    selfie_with_passport = profile['selfie_with_passport']
    monthly_income = profile['monthly_income']
    employment_status = profile['employment_status']
    organization_number = profile['organization_number']
    guarantor_info = profile['guarantor_info']
    guarantor_passport = profile['guarantor_passport']
    category_choice = profile['category_choice']
    product_choice = profile['product_choice']
    cost_product = profile['cost_product']
    installment_terms = profile['installment_terms']

    caption = (f"🔔 Новая заявка.\n\n"
               f"Профиль в телеграм: {user_tg}\n"
               f"Имя: {name}\n"
               f"Фамилия: {surname}\n"
               f"Отчество: {middle_name}\n"
               f"Город прописки: {city_of_registration}\n"
               f"Город проживания: {city_of_residence}\n"
               f"Телефон: {phone_number}\n"
               f"Ежемесячный доход: {monthly_income}\n"
               f"Статус работы: {employment_status}\n"
               f"Номер организации: {organization_number}\n"
               f"Поручитель: {guarantor_info}\n\n"
               f"Категория товара: {category_choice}\n"
               f"Выбранный товар: {product_choice}\n"
               f"Стоимость товара: {cost_product}\n"
               f"Условия рассрочки: {installment_terms}\n")

    media = []

    # Добавление сканов паспорта
    for scan in passport_scans:
        media.append(types.InputMediaPhoto(scan))

    # Добавление селфи с паспортом
    media.append(types.InputMediaPhoto(selfie_with_passport))

    # Добавление сканов паспорта поручителя
    for scan in guarantor_passport[:-1]:
        media.append(types.InputMediaPhoto(scan))

    # Добавление последнего скана паспорта поручителя с описанием
    media.append(types.InputMediaPhoto(guarantor_passport[-1], caption=caption))

    await bot.send_media_group(ADMIN_GROUP, media=media)
    await bot.send_message(ADMIN_GROUP, text='Выберите действие:', reply_markup=kb.get_inline_keyboard(user_id))


@dp.callback_query_handler(text_contains='approve')
async def approve_callback_handler(query: types.CallbackQuery) -> None:
    """
    Обрабатывает команду модеаратора "Одобрить" и отвечает пользователю
    """
    user_id = query.data.split(':')[1]
    await sq.update_profile_status(user_id, status_check=1)
    await query.answer("Анкета одобрена.")
    await bot.edit_message_text(
        chat_id=query.message.chat.id,
        message_id=query.message.message_id,
        text="✅ Заявка одобрена"
        )
    await bot.send_message(user_id, text='Вам одобрена рассрочка!')
    user_data = await sq.get_status(user_id)

    caption = (
        f"Имя: {user_data[1]}\n"
        f"Фамилия: {user_data[2]}\n"
        f"Отчество: {user_data[3]}\n"
        f"Город прописки: {user_data[4]}\n"
        f"Город проживания: {user_data[5]}\n"
        f"Телефон: {user_data[6]}\n"
        f"Ежемесячный доход: {user_data[9]}\n"
        f"Статус работы: {user_data[10]}\n"
        f"Номер организации: {user_data[11]}\n"
        f"Поручитель: {user_data[12]}\n\n"
        f"Категория товара: {user_data[14]}\n"
        f"Выбранный товар: {user_data[15]}\n"
        f"Стоимость товара: {user_data[16]}\n"
        f"Условия рассрочки: {user_data[17]}\n"
    )

    media = []

    try:
        # Преобразование строкового представления списка в список
        passport_scans = ast.literal_eval(user_data[7])
        selfie_with_passport = user_data[8]
        guarantor_passport = ast.literal_eval(user_data[13])

        # Проверка корректности идентификаторов файлов и добавление в media
        for scan in passport_scans:
            if isinstance(scan, str) and len(scan) > 0:
                media.append(types.InputMediaPhoto(scan))
            else:
                logging.error(f"Invalid file identifier for passport scan: {scan}")

        if isinstance(selfie_with_passport, str) and len(selfie_with_passport) > 0:
            media.append(types.InputMediaPhoto(selfie_with_passport))
        else:
            logging.error(f"Invalid file identifier for selfie with passport: {selfie_with_passport}")

        for scan in guarantor_passport[:-1]:
            if isinstance(scan, str) and len(scan) > 0:
                media.append(types.InputMediaPhoto(scan))
            else:
                logging.error(f"Invalid file identifier for guarantor passport scan: {scan}")

        if isinstance(guarantor_passport[-1], str) and len(guarantor_passport[-1]) > 0:
            media.append(types.InputMediaPhoto(guarantor_passport[-1], caption=caption))
        else:
            logging.error(f"Invalid file identifier for last guarantor passport scan: {guarantor_passport[-1]}")
    except (SyntaxError, ValueError) as e:
        logging.error(f"Error parsing file identifiers: {e}")

    if media:
        try:
            await bot.send_media_group(APPROVE_GROUP, media=media)
        except Exception as e:
            logging.error(f"Error sending media group: {e}")
    else:
        logging.error("No valid media to send.")


@dp.callback_query_handler(text_contains='reject')
async def reject_callback_handler(query: types.CallbackQuery) -> None:
    """
    Обрабатывает команду модератора "Отклонить" и отвечает пользователю
    """
    user_id = query.data.split(':')[1]
    await sq.update_profile_status(user_id, status_check=2)
    await bot.send_message(
        user_id,
        text=('К сожалению Ваша заявка отклонена модератором!')
        )
    await query.answer("Анкета отклонена.")
    await bot.edit_message_text(
        chat_id=query.message.chat.id,
        message_id=query.message.message_id,
        text=" ❌ Заявка отклонена"
        )
    

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    executor.start_polling(dp,
                           skip_updates=True,
                           on_startup=on_startup)