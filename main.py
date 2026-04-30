import asyncio
import logging
import random
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web
from utils.db import Database
import config

# MongoDB ulanish kodi
MONGO_URI = "mongodb+srv://Dimajon:DD1559831DD@cluster0.dty9eag.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
db = Database(MONGO_URI)

PREMIUM_MARK = "⭐️"

# --- Tillar lug'ati ---
TEXTS = {
    "uz": {
        "welcome": "Xush kelibsiz!",
        "main_menu": "Asosiy menyu",
        "search": "Qidiruv 🔍",
        "profile": "Profilim 👤",
        "settings": "Sozlamalar ⚙️",
        "edit_profile": "Profilni tahrirlash 📝",
        "back": "Orqaga ⬅️",
        "find_boy": "Yigit topish 🧒",
        "find_girl": "Qiz topish 🧕",
        "next": "Keyingisi ⏭",
        "send_msg": "Xabar yuborish ✉️",
        "end_chat": "Suhbatni yakunlash ❌",
        "enter_name": "Ismingizni kiriting:",
        "enter_age": "Yoshingizni kiriting:",
        "select_gender": "Jinsingizni tanlang:",
        "select_region": "Viloyatingizni tanlang:",
        "send_photo": "Profilingiz uchun rasm yuboring:",
        "reg_done": "Ro'yxatdan o'tish yakunlandi!",
        "no_one": "Hozircha hech kim topilmadi.",
        "msg_sent": "Xabaringiz yetkazildi! ✅",
        "reply": "Javob berish ✍️",
        "chat_started": "bilan suhbat boshlandi. Xabaringizni yozing:",
        "link_forbidden": "Link yuborish taqiqlangan! 🚫"
    },
    "ru": {
        "welcome": "Добро пожаловать!",
        "main_menu": "Главное меню",
        "search": "Поиск 🔍",
        "profile": "Мой профиль 👤",
        "settings": "Настройки ⚙️",
        "edit_profile": "Редактировать профиль 📝",
        "back": "Назад ⬅️",
        "find_boy": "Найти парня 🧒",
        "find_girl": "Найти девушку 🧕",
        "next": "Следующий ⏭",
        "send_msg": "Отправить сообщение ✉️",
        "end_chat": "Завершить чат ❌",
        "enter_name": "Введите ваше имя:",
        "enter_age": "Введите ваш возраст:",
        "select_gender": "Выберите ваш пол:",
        "select_region": "Выберите ваш регион:",
        "send_photo": "Отправьте фото для профиля:",
        "reg_done": "Регистрация завершена!",
        "no_one": "Пока никого не найдено.",
        "msg_sent": "Ваше сообщение доставлено! ✅",
        "reply": "Ответить ✍️",
        "chat_started": "чат начат. Введите ваше сообщение:",
        "link_forbidden": "Отправка ссылок запрещена! 🚫"
    },
    "en": {
        "welcome": "Welcome!",
        "main_menu": "Main menu",
        "search": "Search 🔍",
        "profile": "My profile 👤",
        "settings": "Settings ⚙️",
        "edit_profile": "Edit profile 📝",
        "back": "Back ⬅️",
        "find_boy": "Find a boy 🧒",
        "find_girl": "Find a girl 🧕",
        "next": "Next ⏭",
        "send_msg": "Send message ✉️",
        "end_chat": "End chat ❌",
        "enter_name": "Enter your name:",
        "enter_age": "Enter your age:",
        "select_gender": "Select your gender:",
        "select_region": "Select your region:",
        "send_photo": "Send a photo for your profile:",
        "reg_done": "Registration completed!",
        "no_one": "No one found yet.",
        "msg_sent": "Your message has been delivered! ✅",
        "reply": "Reply ✍️",
        "chat_started": "chat started. Enter your message:",
        "link_forbidden": "Sending links is forbidden! 🚫"
    }
}

class Registration(StatesGroup):
    language, name, age, gender, region, photo = State(), State(), State(), State(), State(), State()

class EditProfile(StatesGroup):
    choosing_field, updating_value = State(), State()

class SearchState(StatesGroup):
    browsing, chatting = State(), State()

# --- Klaviaturalar ---
def get_lang_kb():
    kb = [[types.KeyboardButton(text="O'zbekcha 🇺🇿"), types.KeyboardButton(text="Русский 🇷🇺"), types.KeyboardButton(text="English 🇺🇸")]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_main_menu(lang):
    t = TEXTS[lang]
    kb = [[types.KeyboardButton(text=t["search"]), types.KeyboardButton(text=t["profile"])],
          [types.KeyboardButton(text=t["settings"])]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_search_menu_kb(lang):
    t = TEXTS[lang]
    kb = [[types.KeyboardButton(text=t["find_boy"]), types.KeyboardButton(text=t["find_girl"])],
          [types.KeyboardButton(text=t["back"])]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_profile_kb(lang):
    t = TEXTS[lang]
    kb = [[types.KeyboardButton(text=t["edit_profile"])], [types.KeyboardButton(text=t["back"])]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_chat_kb(lang):
    t = TEXTS[lang]
    kb = [[types.KeyboardButton(text=t["send_msg"]), types.KeyboardButton(text=t["next"])],
          [types.KeyboardButton(text=t["back"])]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_active_chat_kb(lang):
    t = TEXTS[lang]
    kb = [[types.KeyboardButton(text=t["end_chat"])]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_reply_button(target_id, lang):
    builder = InlineKeyboardBuilder()
    builder.button(text=TEXTS[lang]["reply"], callback_data=f"reply_{target_id}")
    return builder.as_markup()

# --- Handlerlar ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Tilni tanlang / Выберите язык / Select language:", reply_markup=get_lang_kb())
        await state.set_state(Registration.language)
    else:
        lang = user.get('lang', 'uz')
        await message.answer(f"{TEXTS[lang]['welcome']}, {user.get('full_name')} {PREMIUM_MARK}!", reply_markup=get_main_menu(lang))

@dp.message(Registration.language)
async def set_lang(message: types.Message, state: FSMContext):
    lang = "uz" if "O'zbekcha" in message.text else ("ru" if "Русский" in message.text else "en")
    await db.add_user(message.from_user.id, message.from_user.username, lang)
    await state.update_data(lang=lang)
    await message.answer(TEXTS[lang]["enter_name"])
    await state.set_state(Registration.name)

@dp.message(Registration.name)
async def set_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'uz')
    await db.update_user(message.from_user.id, full_name=message.text)
    await message.answer(TEXTS[lang]["enter_age"])
    await state.set_state(Registration.age)

# ... (Qolgan handlerlar ham shunday TEXTS[lang] orqali yangilanadi) ...
# To'liq kodni GitHub-ga yuklang.

async def handle(request): return web.Response(text="Bot is running!")
async def main():
    try:
        await db.client.admin.command('ping')
        logging.info("MongoDB-ga muvaffaqiyatli ulanildi! ✅")
    except Exception as e:
        logging.error(f"MongoDB ulanishida xatolik: {e} ❌")
        return
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 10000))).start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
