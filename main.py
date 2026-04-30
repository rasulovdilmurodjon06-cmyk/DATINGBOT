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
        "stats": "Botda: 🧒 {boys} yigit va 🧕 {girls} qiz bor",
        "search": "Qidiruv 🔍",
        "profile": "Profilim 👤",
        "settings": "Sozlamalar ⚙️",
        "back": "Orqaga ⬅️",
        "find_boy": "Yigit topish 🧒",
        "find_girl": "Qiz topish 🧕",
        "next": "Keyingisi ⏭",
        "send_msg": "Xabar yuborish ✉️",
        "edit_profile": "Profilni tahrirlash 📝",
        "enter_name": "Ismingizni kiriting:",
        "enter_age": "Yoshingizni kiriting:",
        "select_gender": "Jinsingizni tanlang:",
        "select_region": "Viloyatingizni tanlang:",
        "send_photo": "Profilingiz uchun rasm yuboring:",
        "no_one": "Hozircha hech kim topilmadi.",
        "reply": "Javob berish ✍️"
    },
    "ru": {
        "welcome": "Добро пожаловать!",
        "stats": "В боте: 🧒 {boys} парней и 🧕 {girls} девушек",
        "search": "Поиск 🔍",
        "profile": "Мой профиль 👤",
        "settings": "Настройки ⚙️",
        "back": "Назад ⬅️",
        "find_boy": "Найти парня 🧒",
        "find_girl": "Найти девушку 🧕",
        "next": "Следующий ⏭",
        "send_msg": "Отправить сообщение ✉️",
        "edit_profile": "Редактировать профиль 📝",
        "enter_name": "Введите ваше имя:",
        "enter_age": "Введите ваш возраст:",
        "select_gender": "Выберите ваш пол:",
        "select_region": "Выберите ваш регион:",
        "send_photo": "Отправьте фото для профиля:",
        "no_one": "Пока никого не найдено.",
        "reply": "Ответить ✍️"
    },
    "en": {
        "welcome": "Welcome!",
        "stats": "In bot: 🧒 {boys} boys and 🧕 {girls} girls",
        "search": "Search 🔍",
        "profile": "My profile 👤",
        "settings": "Settings ⚙️",
        "back": "Back ⬅️",
        "find_boy": "Find a boy 🧒",
        "find_girl": "Find a girl 🧕",
        "next": "Next ⏭",
        "send_msg": "Send message ✉️",
        "edit_profile": "Edit profile 📝",
        "enter_name": "Enter your name:",
        "enter_age": "Enter your age:",
        "select_gender": "Select your gender:",
        "select_region": "Select your region:",
        "send_photo": "Send a photo for your profile:",
        "no_one": "No one found yet.",
        "reply": "Reply ✍️"
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

def get_edit_fields_kb(lang):
    t = TEXTS[lang]
    kb = [[types.KeyboardButton(text="Ism/Имя/Name"), types.KeyboardButton(text="Yosh/Возраст/Age")],
          [types.KeyboardButton(text="Viloyat/Регион/Region"), types.KeyboardButton(text="Rasm/Фото/Photo")],
          [types.KeyboardButton(text="Jins/Пол/Gender"), types.KeyboardButton(text="Til/Язык/Language")],
          [types.KeyboardButton(text=t["back"])]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_regions_kb(lang):
    buttons = [types.KeyboardButton(text=r) for r in config.REGIONS]
    kb = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    kb.append([types.KeyboardButton(text=TEXTS[lang]["back"])])
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_gender_kb():
    kb = [[types.KeyboardButton(text="Yigit 🧒 / Парень"), types.KeyboardButton(text="Qiz 🧕 / Девушка")]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_chat_kb(lang):
    t = TEXTS[lang]
    kb = [[types.KeyboardButton(text=t["send_msg"]), types.KeyboardButton(text=t["next"])],
          [types.KeyboardButton(text=t["back"])]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- Handlerlar ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Tilni tanlang / Выберите язык / Select language:", reply_markup=get_lang_kb())
        await state.set_state(Registration.language)
    else:
        lang = user.get('lang', 'uz')
        boys = await db.users.count_documents({'gender': 'male'})
        girls = await db.users.count_documents({'gender': 'female'})
        stats = TEXTS[lang]["stats"].format(boys=boys, girls=girls)
        await message.answer(f"{TEXTS[lang]['welcome']} {PREMIUM_MARK}\n\n{stats}", reply_markup=get_main_menu(lang))

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

@dp.message(Registration.age)
async def set_age(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'uz')
    if not message.text.isdigit(): return await message.answer(TEXTS[lang]["enter_age"])
    await db.update_user(message.from_user.id, age=int(message.text))
    await message.answer(TEXTS[lang]["select_gender"], reply_markup=get_gender_kb())
    await state.set_state(Registration.gender)

@dp.message(Registration.gender)
async def set_gender(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'uz')
    gender = "male" if "Yigit" in message.text else "female"
    await db.update_user(message.from_user.id, gender=gender)
    await message.answer(TEXTS[lang]["select_region"], reply_markup=get_regions_kb(lang))
    await state.set_state(Registration.region)

@dp.message(Registration.region)
async def set_region(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'uz')
    await db.update_user(message.from_user.id, region=message.text)
    await message.answer(TEXTS[lang]["send_photo"], reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(Registration.photo)

@dp.message(Registration.photo, F.photo)
async def set_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'uz')
    await db.update_user(message.from_user.id, photo=message.photo[-1].file_id)
    await message.answer(f"✅ {TEXTS[lang]['welcome']}", reply_markup=get_main_menu(lang))
    await state.clear()

@dp.message(F.text.in_(["Qidiruv 🔍", "Поиск 🔍", "Search 🔍"]))
async def search_menu(message: types.Message):
    user = await db.get_user(message.from_user.id)
    lang = user.get('lang', 'uz')
    await message.answer(TEXTS[lang]["search"], reply_markup=get_search_menu_kb(lang))

@dp.message(F.text.in_(["Yigit topish 🧒", "Найти парня 🧒", "Find a boy 🧒", "Qiz topish 🧕", "Найти девушку 🧕", "Find a girl 🧕", "Keyingisi ⏭", "Следующий ⏭", "Next ⏭"]))
async def find_partner(message: types.Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user.get('lang', 'uz')
    data = await state.get_data()
    
    if "Keyingisi" in message.text or "Следующий" in message.text or "Next" in message.text:
        gender = data.get('search_gender')
    else:
        gender = "male" if ("Yigit" in message.text or "парня" in message.text or "boy" in message.text) else "female"
        await state.update_data(search_gender=gender)
    
    if not gender: return await message.answer(TEXTS[lang]["search"], reply_markup=get_search_menu_kb(lang))

    users = await db.get_random_users(gender)
    if not users: return await message.answer(TEXTS[lang]["no_one"], reply_markup=get_search_menu_kb(lang))
    
    partner = random.choice(users)
    await state.update_data(target_id=partner['user_id'], is_fake=partner.get('is_fake', 0))
    caption = f"👤 {partner['full_name']} {PREMIUM_MARK}, {partner['age']}\n📍 {partner['region']}"
    if partner.get('photo'): await message.answer_photo(partner['photo'], caption=caption, reply_markup=get_chat_kb(lang))
    else: await message.answer(caption, reply_markup=get_chat_kb(lang))
    await state.set_state(SearchState.browsing)

@dp.message(F.text.in_(["Profilim 👤", "Мой профиль 👤", "My profile 👤"]))
async def my_profile(message: types.Message):
    user = await db.get_user(message.from_user.id)
    lang = user.get('lang', 'uz')
    gender_text = "Yigit 🧒" if user.get('gender') == "male" else "Qiz 🧕"
    caption = f"👤 {user.get('full_name')} {PREMIUM_MARK}\n🔢 {user.get('age')}\n📍 {user.get('region')}\n🚻 {gender_text}"
    if user.get('photo'): await message.answer_photo(user['photo'], caption=caption, reply_markup=get_profile_kb(lang))
    else: await message.answer(caption, reply_markup=get_profile_kb(lang))

@dp.message(F.text.in_(["Sozlamalar ⚙️", "Настройки ⚙️", "Settings ⚙️"]))
async def settings_menu(message: types.Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user.get('lang', 'uz')
    await message.answer(TEXTS[lang]["settings"], reply_markup=get_edit_fields_kb(lang))
    await state.set_state(EditProfile.choosing_field)

@dp.message(F.text.in_(["Orqaga ⬅️", "Назад ⬅️", "Back ⬅️"]))
async def go_back(message: types.Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user.get('lang', 'uz')
    await state.clear()
    await message.answer(TEXTS[lang]["main_menu"], reply_markup=get_main_menu(lang))

# Render veb-server
async def handle(request): return web.Response(text="Bot is running!")
async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 10000))).start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    
