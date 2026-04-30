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

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)

# Bot va Dispatcher obyektlari
bot = Bot(token=config.API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
db = Database(config.DB_NAME)

# Holatlar (States)
class Registration(StatesGroup):
    language = State()
    name = State()
    age = State()
    gender = State()
    region = State()
    photo = State()

class EditProfile(StatesGroup):
    choosing_field = State()
    updating_value = State()

class SearchState(StatesGroup):
    browsing = State()
    chatting = State()

# --- Klaviaturalar ---
def get_main_menu():
    kb = [[types.KeyboardButton(text="Qidiruv 🔍"), types.KeyboardButton(text="Profilim 👤")],
          [types.KeyboardButton(text="Sozlamalar ⚙️")]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_profile_kb():
    kb = [[types.KeyboardButton(text="Profilni tahrirlash 📝")],
          [types.KeyboardButton(text="Orqaga ⬅️")]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_edit_fields_kb():
    kb = [[types.KeyboardButton(text="Ismni o'zgartirish"), types.KeyboardButton(text="Yoshni o'zgartirish")],
          [types.KeyboardButton(text="Viloyatni o'zgartirish"), types.KeyboardButton(text="Rasmni o'zgartirish")],
          [types.KeyboardButton(text="Orqaga ⬅️")]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_regions_kb():
    buttons = [types.KeyboardButton(text=r) for r in config.REGIONS]
    kb = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    kb.append([types.KeyboardButton(text="Orqaga ⬅️")])
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_chat_buttons(target_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="Javob berish ✍️", callback_data=f"reply_{target_id}")
    return builder.as_markup()

# --- Handlerlar ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    if not user:
        kb = [[types.KeyboardButton(text="O'zbekcha 🇺🇿"), types.KeyboardButton(text="English 🇺🇸")]]
        await message.answer("Assalomu alaykum! Botga xush kelibsiz. Iltimos, tilni tanlang:", 
                           reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))
        await state.set_state(Registration.language)
    else:
        await message.answer("Xush kelibsiz!", reply_markup=get_main_menu())

@dp.message(F.text == "Orqaga ⬅️")
async def go_back(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyu:", reply_markup=get_main_menu())

# --- Ro'yxatdan o'tish ---
@dp.message(Registration.language)
async def set_lang(message: types.Message, state: FSMContext):
    lang = "uz" if "O'zbekcha" in message.text else "en"
    db.add_user(message.from_user.id, message.from_user.username, lang)
    await message.answer("Ismingizni kiriting:")
    await state.set_state(Registration.name)

@dp.message(Registration.name)
async def set_name(message: types.Message, state: FSMContext):
    db.update_user(message.from_user.id, full_name=message.text)
    await message.answer("Yoshingizni kiriting:")
    await state.set_state(Registration.age)

@dp.message(Registration.age)
async def set_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Iltimos, faqat raqam kiriting:")
    db.update_user(message.from_user.id, age=int(message.text))
    kb = [[types.KeyboardButton(text="Yigit 🧒"), types.KeyboardButton(text="Qiz 🧕")]]
    await message.answer("Jinsingizni tanlang:", reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))
    await state.set_state(Registration.gender)

@dp.message(Registration.gender)
async def set_gender(message: types.Message, state: FSMContext):
    gender = "male" if "Yigit" in message.text else "female"
    db.update_user(message.from_user.id, gender=gender)
    await message.answer("Viloyatingizni tanlang:", reply_markup=get_regions_kb())
    await state.set_state(Registration.region)

@dp.message(Registration.region)
async def set_region(message: types.Message, state: FSMContext):
    db.update_user(message.from_user.id, region=message.text)
    await message.answer("Profilingiz uchun rasm yuboring:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(Registration.photo)

@dp.message(Registration.photo, F.photo)
async def set_photo(message: types.Message, state: FSMContext):
    db.update_user(message.from_user.id, photo=message.photo[-1].file_id)
    await message.answer("Ro'yxatdan o'tish muvaffaqiyatli yakunlandi! ✅", reply_markup=get_main_menu())
    await state.clear()

# --- Profil va Tahrirlash ---
@dp.message(F.text == "Profilim 👤")
async def my_profile(message: types.Message):
    user = db.get_user(message.from_user.id)
    caption = f"👤 Ism: {user[2]}\n🔢 Yosh: {user[3]}\n📍 Viloyat: {user[5]}"
    if user[7]:
        await message.answer_photo(user[7], caption=caption, reply_markup=get_profile_kb())
    else:
        await message.answer(caption, reply_markup=get_profile_kb())

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
    else: return
    await state.set_state(EditProfile.updating_value)

@dp.message(EditProfile.updating_value)
async def update_value(message: types.Message, state: FSMContext):
    data = await state.get_data()
    field = data['field']
    val = message.photo[-1].file_id if field == "photo" and message.photo else message.text
    db.update_user(message.from_user.id, **{field: val})
    await message.answer("O'zgartirildi! ✅", reply_markup=get_main_menu())
    await state.clear()

# --- Qidiruv va Anonim Chat ---
@dp.message(F.text == "Qidiruv 🔍")
async def search_menu(message: types.Message):
    kb = [[types.KeyboardButton(text="Yigit topish 🧒"), types.KeyboardButton(text="Qiz topish 🧕")], 
          [types.KeyboardButton(text="Orqaga ⬅️")]]
    await message.answer("Kimni qidiramiz?", reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))

@dp.message(F.text.in_(["Yigit topish 🧒", "Qiz topish 🧕"]))
async def find_partner(message: types.Message, state: FSMContext):
    gender = "male" if "Yigit" in message.text else "female"
    users = db.get_random_users(gender)
    if not users:
        return await message.answer("Hozircha hech kim topilmadi.")
    
    user = random.choice(users)
    await state.update_data(target_id=user[0], is_fake=user[9])
    
    kb = [[types.KeyboardButton(text="Xabar yuborish ✉️"), types.KeyboardButton(text="Keyingisi ⏭")], 
          [types.KeyboardButton(text="Orqaga ⬅️")]]
    caption = f"👤 {user[2]}, {user[3]} yosh\n📍 {user[5]}"
    if user[7]:
        await message.answer_photo(user[7], caption=caption, reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))
    else:
        await message.answer(caption, reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))
    await state.set_state(SearchState.browsing)

@dp.message(SearchState.browsing, F.text == "Xabar yuborish ✉️")
async def start_chat(message: types.Message, state: FSMContext):
    await message.answer("Xabaringizni yozing (u odamga darhol boradi):", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(SearchState.chatting)

@dp.message(SearchState.chatting)
async def send_message_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    target_id = data.get('target_id')
    
    if data.get('is_fake'):
        await message.answer("Xabar yuborildi! ✅")
        await asyncio.sleep(2)
        await message.answer(f"Javob: {random.choice(['Salom!', 'Qayerdansiz?', 'Tanishganimdan xursandman 😊'])}")
    else:
        try:
            await bot.send_message(
                chat_id=target_id, 
                text=f"📩 Yangi xabar!\n\nSiz bilan kimdir suhbatlashmoqchi:\n\"{message.text}\"",
                reply_markup=get_chat_buttons(message.from_user.id)
            )
            await message.answer("Xabaringiz yetkazildi! ✅")
        except:
            await message.answer("Xabar yuborib bo'lmadi. ❌")
    
    await message.answer("Asosiy menyu", reply_markup=get_main_menu())
    await state.clear()

@dp.callback_query(F.data.startswith("reply_"))
async def reply_callback(callback: types.CallbackQuery, state: FSMContext):
    target_id = int(callback.data.split("_")[1])
    await callback.message.answer("Javob xabaringizni yozing:")
    await state.update_data(target_id=target_id)
    await state.set_state(SearchState.chatting)
    await callback.answer()

# Link filtri
@dp.message(F.text.contains("t.me") | F.text.contains("http") | F.text.contains("@"))
async def link_filter(message: types.Message):
    await message.delete()
    await message.answer("Link yuborish taqiqlangan! 🚫")

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
    
