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

# Premium belgi
PREMIUM_MARK = "⭐️"

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

def get_main_menu():
    kb = [[types.KeyboardButton(text="Qidiruv 🔍"), types.KeyboardButton(text="Profilim 👤")],
          [types.KeyboardButton(text="Sozlamalar ⚙️")]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_search_menu_kb():
    kb = [[types.KeyboardButton(text="Yigit topish 🧒"), types.KeyboardButton(text="Qiz topish 🧕")],
          [types.KeyboardButton(text="Orqaga ⬅️")]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_profile_kb():
    kb = [[types.KeyboardButton(text="Profilni tahrirlash 📝")], [types.KeyboardButton(text="Orqaga ⬅️")]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_edit_fields_kb():
    kb = [[types.KeyboardButton(text="Ismni o'zgartirish"), types.KeyboardButton(text="Yoshni o'zgartirish")],
          [types.KeyboardButton(text="Viloyatni o'zgartirish"), types.KeyboardButton(text="Rasmni o'zgartirish")],
          [types.KeyboardButton(text="Jinsni o'zgartirish"), types.KeyboardButton(text="Tilni o'zgartirish")],
          [types.KeyboardButton(text="Orqaga ⬅️")]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_regions_kb():
    buttons = [types.KeyboardButton(text=r) for r in config.REGIONS]
    kb = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    kb.append([types.KeyboardButton(text="Orqaga ⬅️")])
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_gender_kb():
    kb = [[types.KeyboardButton(text="Yigit 🧒"), types.KeyboardButton(text="Qiz 🧕")]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_chat_kb():
    kb = [[types.KeyboardButton(text="Xabar yuborish ✉️"), types.KeyboardButton(text="Keyingisi ⏭")],
          [types.KeyboardButton(text="Orqaga ⬅️")]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_active_chat_kb():
    kb = [[types.KeyboardButton(text="Suhbatni yakunlash ❌")]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_reply_button(target_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="Javob berish ✍️", callback_data=f"reply_{target_id}")
    return builder.as_markup()

# --- Handlerlar ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Assalomu alaykum! Botga xush kelibsiz. Tilni tanlang / Выберите язык / Select language:", 
                           reply_markup=get_lang_kb())
        await state.set_state(Registration.language)
    else:
        await message.answer(f"Xush kelibsiz, {user.get('full_name')} {PREMIUM_MARK}!", reply_markup=get_main_menu())

@dp.message(F.text == "Orqaga ⬅️")
async def go_back(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyu:", reply_markup=get_main_menu())

@dp.message(F.text == "Suhbatni yakunlash ❌")
async def end_chat(message: types.Message, state: FSMContext):
    data = await state.get_data()
    target_id = data.get('target_id')
    if target_id:
        try: await bot.send_message(target_id, "Suhbatdosh suhbatni yakunladi. ❌", reply_markup=get_main_menu())
        except: pass
    await state.clear()
    await message.answer("Suhbat yakunlandi.", reply_markup=get_main_menu())

# --- Ro'yxatdan o'tish ---
@dp.message(Registration.language)
async def set_lang(message: types.Message, state: FSMContext):
    lang = "uz" if "O'zbekcha" in message.text else ("ru" if "Русский" in message.text else "en")
    await db.add_user(message.from_user.id, message.from_user.username, lang)
    await message.answer("Ismingizni kiriting / Введите ваше имя / Enter your name:")
    await state.set_state(Registration.name)

@dp.message(Registration.name)
async def set_name(message: types.Message, state: FSMContext):
    await db.update_user(message.from_user.id, full_name=message.text)
    await message.answer("Yoshingizni kiriting / Введите ваш возраст / Enter your age:")
    await state.set_state(Registration.age)

@dp.message(Registration.age)
async def set_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("Faqat raqam kiriting / Только цифры / Numbers only:")
    await db.update_user(message.from_user.id, age=int(message.text))
    await message.answer("Jinsingizni tanlang / Выберите ваш пол / Select your gender:", reply_markup=get_gender_kb())
    await state.set_state(Registration.gender)

@dp.message(Registration.gender)
async def set_gender(message: types.Message, state: FSMContext):
    gender = "male" if "Yigit" in message.text else "female"
    await db.update_user(message.from_user.id, gender=gender)
    await message.answer("Viloyatingizni tanlang / Выберите ваш регион / Select your region:", reply_markup=get_regions_kb())
    await state.set_state(Registration.region)

@dp.message(Registration.region)
async def set_region(message: types.Message, state: FSMContext):
    await db.update_user(message.from_user.id, region=message.text)
    await message.answer("Profilingiz uchun rasm yuboring / Отправьте фото для профиля / Send a photo for your profile:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(Registration.photo)

@dp.message(Registration.photo, F.photo)
async def set_photo(message: types.Message, state: FSMContext):
    await db.update_user(message.from_user.id, photo=message.photo[-1].file_id)
    await message.answer(f"Ro'yxatdan o'tish yakunlandi! {PREMIUM_MARK} ✅", reply_markup=get_main_menu())
    await state.clear()

# --- Profil va Sozlamalar ---
@dp.message(F.text == "Profilim 👤")
async def my_profile(message: types.Message):
    user = await db.get_user(message.from_user.id)
    if not user: return await message.answer("Profil topilmadi. /start bosing.")
    gender_text = "Yigit 🧒" if user.get('gender') == "male" else "Qiz 🧕"
    caption = f"👤 Ism: {user.get('full_name')} {PREMIUM_MARK}\n🔢 Yosh: {user.get('age')}\n📍 Viloyat: {user.get('region')}\n🚻 Jins: {gender_text}"
    if user.get('photo'): await message.answer_photo(user['photo'], caption=caption, reply_markup=get_profile_kb())
    else: await message.answer(caption, reply_markup=get_profile_kb())

@dp.message(F.text == "Sozlamalar ⚙️")
async def settings_menu(message: types.Message):
    await message.answer("Sozlamalar bo'limi:", reply_markup=get_profile_kb())

@dp.message(F.text == "Profilni tahrirlash 📝")
async def edit_profile(message: types.Message, state: FSMContext):
    await message.answer("Nimani o'zgartiramiz?", reply_markup=get_edit_fields_kb())
    await state.set_state(EditProfile.choosing_field)

@dp.message(EditProfile.choosing_field)
async def choose_field(message: types.Message, state: FSMContext):
    if "Ism" in message.text:
        await message.answer("Yangi ismni kiriting:")
        await state.update_data(field="full_name")
    elif "Yosh" in message.text:
        await message.answer("Yangi yoshni kiriting:")
        await state.update_data(field="age")
    elif "Viloyat" in message.text:
        await message.answer("Yangi viloyatni tanlang:", reply_markup=get_regions_kb())
        await state.update_data(field="region")
    elif "Rasm" in message.text:
        await message.answer("Yangi rasm yuboring:")
        await state.update_data(field="photo")
    elif "Jins" in message.text:
        await message.answer("Jinsingizni tanlang:", reply_markup=get_gender_kb())
        await state.update_data(field="gender")
    elif "Til" in message.text:
        await message.answer("Tilni tanlang:", reply_markup=get_lang_kb())
        await state.update_data(field="lang")
    elif "Orqaga" in message.text: return await go_back(message, state)
    else: return
    await state.set_state(EditProfile.updating_value)

@dp.message(EditProfile.updating_value)
async def update_value(message: types.Message, state: FSMContext):
    data = await state.get_data()
    field = data['field']
    if field == "photo" and message.photo:
        val = message.photo[-1].file_id
    elif field == "gender":
        val = "male" if "Yigit" in message.text else "female"
    elif field == "lang":
        val = "uz" if "O'zbekcha" in message.text else ("ru" if "Русский" in message.text else "en")
    else:
        val = message.text
    
    await db.update_user(message.from_user.id, **{field: val})
    await message.answer(f"O'zgartirildi! {PREMIUM_MARK} ✅", reply_markup=get_main_menu())
    await state.clear()

# --- Qidiruv va Chat ---
@dp.message(F.text == "Qidiruv 🔍")
async def search_menu(message: types.Message):
    await message.answer("Kimni qidiramiz?", reply_markup=get_search_menu_kb())

@dp.message(F.text.in_(["Yigit topish 🧒", "Qiz topish 🧕"]) | (F.text == "Keyingisi ⏭"))
async def find_partner(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if message.text == "Keyingisi ⏭":
        gender = data.get('search_gender')
    else:
        gender = "male" if "Yigit" in message.text else "female"
        await state.update_data(search_gender=gender)
    
    if not gender: return await message.answer("Iltimos, qidiruv turini tanlang:", reply_markup=get_search_menu_kb())

    users = await db.get_random_users(gender)
    if not users: return await message.answer("Hozircha hech kim topilmadi.", reply_markup=get_search_menu_kb())
    
    user = random.choice(users)
    await state.update_data(target_id=user['user_id'], is_fake=user.get('is_fake', 0))
    caption = f"👤 {user['full_name']} {PREMIUM_MARK}, {user['age']} yosh\n📍 {user['region']}"
    if user.get('photo'): await message.answer_photo(user['photo'], caption=caption, reply_markup=get_chat_kb())
    else: await message.answer(caption, reply_markup=get_chat_kb())
    await state.set_state(SearchState.browsing)

@dp.message(SearchState.browsing)
async def browsing(message: types.Message, state: FSMContext):
    if message.text == "Keyingisi ⏭": await find_partner(message, state)
    elif message.text == "Xabar yuborish ✉️":
        await message.answer("Xabaringizni yozing (suhbat boshlanadi):", reply_markup=get_active_chat_kb())
        await state.set_state(SearchState.chatting)
    elif message.text == "Orqaga ⬅️": await go_back(message, state)

@dp.message(SearchState.chatting)
async def chatting_handler(message: types.Message, state: FSMContext):
    if message.text == "Suhbatni yakunlash ❌": return await end_chat(message, state)
    if message.text and any(x in message.text.lower() for x in ['t.me', 'http', '@']):

await message.delete()
        return await message.answer("Link taqiqlangan! 🚫")
    data = await state.get_data()
    target_id = data.get('target_id')
    if data.get('is_fake'):
        await asyncio.sleep(1)
        await message.answer(f"Javob: {random.choice(['Salom!', 'Qayerdansiz?', 'Tanishganimdan xursandman 😊'])}")
    else:
        try:
            sender = await db.get_user(message.from_user.id)
            await bot.send_message(target_id, f"👤 <b>{sender['full_name']} {PREMIUM_MARK}</b>:\n\"{message.text}\"", 
                                 reply_markup=get_reply_button(message.from_user.id), parse_mode="HTML")
        except: await message.answer("Xabar yuborilmadi. ❌")

@dp.callback_query(F.data.startswith("reply_"))
async def reply_callback(callback: types.CallbackQuery, state: FSMContext):
    target_id = int(callback.data.split("_")[1])
    sender = await db.get_user(target_id)
    await callback.message.answer(f"👤 <b>{sender['full_name']} {PREMIUM_MARK}</b> bilan suhbat boshlandi:", 
                                reply_markup=get_active_chat_kb(), parse_mode="HTML")
    await state.update_data(target_id=target_id)
    await state.set_state(SearchState.chatting)
    await callback.answer()

# Render veb-server
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

if name == 'main':
    asyncio.run(main())
