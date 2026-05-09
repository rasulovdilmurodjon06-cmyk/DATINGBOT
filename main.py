import asyncio
import logging
import random
import os

from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    CallbackQuery
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.db import Database
import config

# =========================
# SETUP
# =========================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
db = Database(config.MONGO_URI)

# =========================
# STATES
# =========================

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

# =========================
# KEYBOARDS
# =========================

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("Qidiruv 🔍"), KeyboardButton("Profilim 👤")],
            [KeyboardButton("Sozlamalar ⚙️")]
        ],
        resize_keyboard=True
    )

def search_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("Yigit topish 🧒"), KeyboardButton("Qiz topish 🧕")],
            [KeyboardButton("Orqaga ⬅️")]
        ],
        resize_keyboard=True
    )

def chat_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("Xabar yuborish ✉️"), KeyboardButton("Keyingisi ⏭")],
            [KeyboardButton("Orqaga ⬅️")]
        ],
        resize_keyboard=True
    )

def active_chat_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton("Suhbatni yakunlash ❌")]],
        resize_keyboard=True
    )

def edit_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("Ismni o'zgartirish"), KeyboardButton("Yoshni o'zgartirish")],
            [KeyboardButton("Viloyatni o'zgartirish"), KeyboardButton("Rasmni o'zgartirish")],
            [KeyboardButton("Orqaga ⬅️")]
        ],
        resize_keyboard=True
    )

def reply_btn(uid):
    kb = InlineKeyboardBuilder()
    kb.button(text="Javob berish ✍️", callback_data=f"reply_{uid}")
    return kb.as_markup()

# =========================
# START
# =========================

@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):

    user = await db.get_user(message.from_user.id)

    if not user:
        await message.answer("Tilni tanlang:", reply_markup=main_menu())
        await state.set_state(Registration.language)
    else:
        await message.answer("Xush kelibsiz!", reply_markup=main_menu())

# =========================
# MENU BACK
# =========================

@dp.message(F.text == "Orqaga ⬅️")
async def back(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyu:", reply_markup=main_menu())

# =========================
# SEARCH MENU FIX
# =========================

@dp.message(F.text == "Qidiruv 🔍")
async def search_menu(message: types.Message, state: FSMContext):
    await state.set_state(SearchState.browsing)
    await message.answer("Kimni qidiramiz?", reply_markup=search_kb())

# =========================
# BROWSING FIX (ENG MUHIM QISM)
# =========================

@dp.message(SearchState.browsing)
async def browsing(message: types.Message, state: FSMContext):

    if message.text == "Orqaga ⬅️":
        await state.clear()
        return await message.answer("Asosiy menyu", reply_markup=main_menu())

    if message.text in ["Yigit topish 🧒", "Qiz topish 🧕"]:
        gender = "male" if "Yigit" in message.text else "female"
        await state.update_data(search_gender=gender)

    data = await state.get_data()
    gender = data.get("search_gender")

    users = await db.get_random_users(gender, exclude_id=message.from_user.id)

    if not users:
        return await message.answer("Hech kim topilmadi 😔")

    user = random.choice(users)

    await state.update_data(
        target_id=user["user_id"],
        is_fake=user.get("is_fake", 0)
    )

    text = f"👤 {user['full_name']}, {user['age']} yosh\n📍 {user['region']}"

    if user.get("photo"):
        await message.answer_photo(user["photo"], caption=text, reply_markup=chat_kb())
    else:
        await message.answer(text, reply_markup=chat_kb())

    await state.set_state(SearchState.chatting)

# =========================
# CHAT
# =========================

@dp.message(SearchState.chatting)
async def chat(message: types.Message, state: FSMContext):

    if message.text == "Suhbatni yakunlash ❌":
        await state.clear()
        return await message.answer("Tugadi ❌", reply_markup=main_menu())

    data = await state.get_data()
    target_id = data.get("target_id")

    if not target_id:
        return await message.answer("User topilmadi")

    try:
        sender = await db.get_user(message.from_user.id)
        name = sender.get("full_name", "Anonim")

        await bot.send_message(
            target_id,
            f"👤 <b>{name}</b>\n\n{message.text}",
            parse_mode="HTML",
            reply_markup=reply_btn(message.from_user.id)
        )

    except Exception as e:
        logging.error(e)
        await message.answer("Yuborilmadi ❌")

# =========================
# REPLY
# =========================

@dp.callback_query(F.data.startswith("reply_"))
async def reply(call: CallbackQuery, state: FSMContext):

    uid = int(call.data.split("_")[1])

    await state.update_data(target_id=uid)
    await state.set_state(SearchState.chatting)

    await call.message.answer("Suhbat boshlandi 💬", reply_markup=active_chat_kb())
    await call.answer()

# =========================
# PROFILE
# =========================

@dp.message(F.text == "Profilim 👤")
async def profile(message: types.Message):

    user = await db.get_user(message.from_user.id)

    if not user:
        return await message.answer("Profil yo‘q")

    text = f"""
👤 {user.get('full_name')}
🔢 {user.get('age')}
📍 {user.get('region')}
"""

    await message.answer(text, reply_markup=edit_kb())

# =========================
# SETTINGS FIX
# =========================

@dp.message(F.text == "Sozlamalar ⚙️")
async def settings(message: types.Message):
    await message.answer("Sozlamalar", reply_markup=edit_kb())

# =========================
# EDIT PROFILE FIX
# =========================

@dp.message(F.text == "Profilni tahrirlash 📝")
async def edit(message: types.Message, state: FSMContext):
    await state.set_state(EditProfile.choosing_field)
    await message.answer("Nimani o‘zgartiramiz?", reply_markup=edit_kb())

@dp.message(EditProfile.choosing_field)
async def choose(message: types.Message, state: FSMContext):

    if "Ism" in message.text:
        await state.update_data(field="full_name")
        await message.answer("Yangi ism:")

    elif "Yosh" in message.text:
        await state.update_data(field="age")
        await message.answer("Yangi yosh:")

    elif "Viloyat" in message.text:
        await state.update_data(field="region")
        await message.answer("Viloyat:")

    elif "Rasm" in message.text:
        await state.update_data(field="photo")
        await message.answer("Rasm yuboring")

    elif "Orqaga" in message.text:
        await state.clear()
        return await message.answer("Menu", reply_markup=main_menu())

    await state.set_state(EditProfile.updating_value)

@dp.message(EditProfile.updating_value)
async def update(message: types.Message, state: FSMContext):

    data = await state.get_data()
    field = data["field"]

    value = message.photo[-1].file_id if field == "photo" else message.text

    await db.update_user(message.from_user.id, **{field: value})

    await state.clear()

    await message.answer("Yangilandi ✅", reply_markup=main_menu())

# =========================
# SERVER
# =========================

async def handle(request):
    return web.Response(text="Bot ON")

async def main():

    await db.client.admin.command("ping")
    logging.info("DB OK")

    app = web.Application()
    app.router.add_get("/", handle)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", 10000))

    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logging.info("Server started")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
