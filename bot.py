from aiogram.types import Message, CallbackQuery
import logging
import pyperclip
import aiogram
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import StatesGroup, State
import sqlite3
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging.handlers

# Логирование.
logger = logging.getLogger(__name__)

# Cоздаёт все промежуточные каталоги, если они не существуют.
logging.basicConfig(  # Чтобы бот работал успешно, создаём конфиг с базовыми данными для бота
    level=logging.INFO,
    format="[%(levelname)-8s %(asctime)s at           %(funcName)s]: %(message)s",
    datefmt="%d.%d.%Y %H:%M:%S",
    handlers=[logging.handlers.RotatingFileHandler("Logs/     TGBot.log", maxBytes=10485760, backupCount=0), logging.StreamHandler()])


# Создаём Telegram бота и диспетчер
Bot = aiogram.Bot("6295883791:AAEYXIEMTrbHlYbq49uL59LPvu8QQdWwAEc")
DP = aiogram.Dispatcher(Bot, storage=MemoryStorage())

# Создаём базу данных
conn = sqlite3.connect('liviritoys_details_bot.db')
cur = conn.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS users(
username TEXT,
full_name TEXT,
email TEXT);""")
    
# Создаём состояния
class UserState(StatesGroup):
    fullName_and_email = State()

# КОГДА ПОЛЬЗОВАТЕЛЬ ПИШЕТ /start
@DP.message_handler(commands=["start"], state="*")
async def start(msg: Message):

    if cur.execute(f"SELECT username FROM users WHERE username='{msg.from_user.username}'").fetchone() is None:
        cur.execute(f"INSERT INTO users ('username') VALUES(?)", (msg.from_user.username,))
        conn.commit()

    await msg.answer("""Привет, я бот для выдачи реквизитов для оплаты продуктов Ливиндеевой Риммы Николаевны. Для начала работы напишите своё ФИО и электронную почту через запятую. 

Пример: "Новикова Екатерина Николаевна, test@mail.com".""")
    await UserState.fullName_and_email.set()

# Функция проверки входящих данных электронной почты и ФИО.
@DP.message_handler(state=UserState.fullName_and_email)
async def adding_fullName_and_email(msg: Message, state: FSMContext):
    fullName_and_email = msg.text.split(",")
    cur.execute(f"INSERT INTO users ('full_name', 'email') VALUES(?, ?)", (fullName_and_email[0], fullName_and_email[1]))
    conn.commit()

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(*[
        InlineKeyboardButton(
            text="Ознакомиться с офертой",
            url="https://docs.google.com/document/d/1rOI9jEOJI-OOOuo4R316FbXbfGqQawhKP34968ZnAog/edit"),
        InlineKeyboardButton(
            text="Ознакомиться с политикой",
            url="https://docs.google.com/document/d/1oLoaoNsXeaX-Iq_z7T6JUO9-so0LpCAVeDGNDT_tqJA/edit"),
        InlineKeyboardButton(
            text="Согласен ✅",
            callback_data="first_documents_agree"),
        InlineKeyboardButton(
            text="Не согласен ❌",
            callback_data="documents_disagree")
        ]
    )
    await msg.answer("Вы согласны с публичной офертой на оказание платных онлайн-услуг и политикой в отношении обработки персональных данных?", reply_markup=keyboard)
    await state.finish()

# Когда пользователь нажимает на кнопку
@DP.callback_query_handler(state="*")
async def callback_worker(call: CallbackQuery, state: FSMContext):
    # КОГДА ПОЛЬЗОВАТЕЛЬ НАЖИМАЕТ КНОПКУ "Согласен ✅ (Третий документ на согласие рассылки)"
    if call.data == "first_documents_agree":
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton(
                text="Ознакомиться с рассылкой",
                url="https://docs.google.com/document/d/1geXswUknRg0H6xEAL3GJJVHNIPqxOonognFmOsoNrTo/edit"
            ),
            InlineKeyboardButton(
                text="Согласен ✅",
                callback_data="second_document_agree"
            ),
            InlineKeyboardButton(
                text="Не согласен ❌",
                callback_data="documents_disagree")
        )

        await call.message.edit_text(
            "Вы согласны на получение информационной и рекламной рассылки?",
            reply_markup=keyboard
        )
        await UserState.next()  # Переходим к следующему состоянию

        # КОГДА ПОЛЬЗОВАТЕЛЬ НАЖИМАЕТ КНОПКУ "Согласен ✅ (Отправка реквизитов)
    elif call.data == "second_document_agree":
        rekvizit_text = """Спасибо за согласие со всеми документами! Реквизиты:
    
Перевод на карту Сбербанка

<code>2202205024500602</code>

на имя Римма Николаевна Л.

либо по номеру телефона

<code>+79607543030</code>


После оплаты не забудьте прислать мне в личное сообщение чек об оплате, где видно сумму и ФИО плательщика"""

        pyperclip.copy(rekvizit_text)  # Копируем данные в буфер обмена

        await call.message.edit_text(
            rekvizit_text,
            parse_mode="html"
        )
        await state.finish()

    elif call.data == "documents_disagree":
        await call.message.edit_text("Для дальнейших действий нужно дать согласие! ❗️")
        await state.finish()

if __name__ == "__main__":  # Если файл запускается как самостоятельный, а не как модуль
    # В консоле будет отоброжён процесс запуска бота
    logger.info("Запускаю бота...")
    executor.start_polling(  # Бот начинает работать
        dispatcher=DP,  # Передаем в функцию диспетчер
        # (диспетчер отвечает за то, чтобы сообщения пользователя доходили до бота)
        on_startup=logger.info("Загрузился успешно!"), skip_updates=True)
    # Если бот успешно загрузился, то в консоль выведется сообщение