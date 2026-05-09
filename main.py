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
# CONFIG
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

def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Qidiruv 🔍"), KeyboardButton(text="Profilim 👤")],
            [KeyboardButton(text="Sozlamalar ⚙️")]
        ],
        resize_keyboard=True
    )

def get_profile_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Profilni tahrirlash 📝")],
            [KeyboardButton(text="Orqaga ⬅️")]
        ],
        resize_keyboard=True
    )

def get_edit_fields_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Ismni o'zgartirish"), KeyboardButton(text="Yoshni o'zgartirish")],
            [KeyboardButton(text="Viloyatni o'zgartirish"), KeyboardButton(text="Rasmni o'zgartirish")],
            [KeyboardButton(text="Orqaga ⬅️")]
        ],
        resize_keyboard=True
    )

def get_regions_kb():
    buttons = [KeyboardButton(text=r) for r in config.REGIONS]
    kb = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    kb.append([KeyboardButton(text="Orqaga ⬅️")])

    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_search_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Yigit topish 🧒"), KeyboardButton(text="Qiz topish 🧕")],
            [KeyboardButton(text="Orqaga ⬅️")]
        ],
        resize_keyboard=True
    )

def get_chat_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Xabar yuborish ✉️"), KeyboardButton(text="Keyingisi ⏭")],
            [KeyboardButton(text="Orqaga ⬅️")]
        ],
        resize_keyboard=True
    )

def get_active_chat_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Suhbatni yakunlash ❌")]],
        resize_keyboard=True
    )

def get_reply_button(target_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="Javob berish ✍️", callback_data=f"reply_{target_id}")
    return builder.as_markup()

# =========================
# START
# =========================

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):

    user = await db.get_user(message.from_user.id)

    if not user:
        kb = [
            [KeyboardButton(text="O'zbekcha 🇺🇿"), KeyboardButton(text="English 🇺🇸")]
        ]

        await message.answer(
            "Assalomu alaykum!\nTilni tanlang:",
            reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        )

        await state.set_state(Registration.language)

    else:
        await message.answer("Xush kelibsiz!", reply_markup=get_main_menu())

# =========================
# BACK
# =========================

@dp.message(F.text == "Orqaga ⬅️")
async def go_back(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyu:", reply_markup=get_main_menu())

# =========================
# END CHAT
# =========================

@dp.message(F.text == "Suhbatni yakunlash ❌")
async def end_chat(message: types.Message, state: FSMContext):

    data = await state.get_data()
    target_id = data.get("target_id")

    if target_id:
        try:
            await bot.send_message(target_id, "Suhbat tugadi ❌", reply_markup=get_main_menu())
        except Exception as e:
            logging.error(e)

    await state.clear()
    await message.answer("Suhbat yakunlandi.", reply_markup=get_main_menu())

# =========================
# REGISTRATION
# =========================

@dp.message(Registration.language)
async def set_lang(message: types.Message, state: FSMContext):

    lang = "uz" if "O'zbekcha" in message.text else "en"

    await db.add_user(message.from_user.id, message.from_user.username, lang)

    await message.answer("Ismingizni kiriting:")
    await state.set_state(Registration.name)

@dp.message(Registration.name)
async def set_name(message: types.Message, state: FSMContext):

    await db.update_user(message.from_user.id, full_name=message.text)

    await message.answer("Yoshingizni kiriting:")
    await state.set_state(Registration.age)

@dp.message(Registration.age)
async def set_age(message: types.Message, state: FSMContext):

    if not message.text.isdigit() or not (10 <= int(message.text) <= 80):
        return await message.answer("Yoshni to‘g‘ri kiriting:")

    await db.update_user(message.from_user.id, age=int(message.text))

    kb = [[KeyboardButton(text="Yigit 🧒"), KeyboardButton(text="Qiz 🧕")]]

    await message.answer("Jinsingiz:", reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))
    await state.set_state(Registration.gender)

@dp.message(Registration.gender)
async def set_gender(message: types.Message, state: FSMContext):

    gender = "male" if "Yigit" in message.text else "female"
    await db.update_user(message.from_user.id, gender=gender)

    await message.answer("Viloyat:", reply_markup=get_regions_kb())
    await state.set_state(Registration.region)

@dp.message(Registration.region)
async def set_region(message: types.Message, state: FSMContext):

    if message.text == "Orqaga ⬅️":
        return await go_back(message, state)

    await db.update_user(message.from_user.id, region=message.text)

    await message.answer("Rasm yuboring 📸", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Registration.photo)

@dp.message(Registration.photo, F.photo)
async def set_photo(message: types.Message, state: FSMContext):

    await db.update_user(message.from_user.id, photo=message.photo[-1].file_id)

    await message.answer("Ro‘yxatdan o‘tish tugadi ✅", reply_markup=get_main_menu())
    await state.clear()

# =========================
# PROFILE
# =========================

@dp.message(F.text == "Profilim 👤")
async def my_profile(message: types.Message):

    user = await db.get_user(message.from_user.id)

    if not user:
        return await message.answer("Profil topilmadi /start bosing")

    caption = (
        f"👤 Ism: {user.get('full_name','-')}\n"
        f"🔢 Yosh: {user.get('age','-')}\n"
        f"📍 Viloyat: {user.get('region','-')}"
    )

    if user.get("photo"):
        await message.answer_photo(user["photo"], caption=caption, reply_markup=get_profile_kb())
    else:
        await message.answer(caption, reply_markup=get_profile_kb())

# =========================
# SEARCH
# =========================

@dp.message(F.text.in_(["Yigit topish 🧒", "Qiz topish 🧕"]))
async def find_partner(message: types.Message, state: FSMContext):

    gender = "male" if "Yigit" in message.text else "female"

    users = await db.get_random_users(gender, exclude_id=message.from_user.id)

    if not users:
        return await message.answer("Hech kim topilmadi 😔")

    user = random.choice(users)

    await state.update_data(target_id=user["user_id"], is_fake=user.get("is_fake", 0))

    caption = f"👤 {user['full_name']}, {user['age']} yosh\n📍 {user['region']}"

    if user.get("photo"):
        await message.answer_photo(user["photo"], caption=caption, reply_markup=get_chat_kb())
    else:
        await message.answer(caption, reply_markup=get_chat_kb())

    await state.set_state(SearchState.browsing)

# =========================
# CHAT HANDLER
# =========================

@dp.message(SearchState.chatting)
async def chatting(message: types.Message, state: FSMContext):

    if message.text == "Suhbatni yakunlash ❌":
        return await end_chat(message, state)

    data = await state.get_data()
    target_id = data.get("target_id")

    if not target_id:
        return await message.answer("Foydalanuvchi yo‘q")

    try:
        sender = await db.get_user(message.from_user.id)
        name = sender.get("full_name", "Anonim")

        safe_name = name.replace("<", "").replace(">", "")

        await bot.send_message(
            target_id,
            f"👤 <b>{safe_name}</b>\n\n{message.text}",
            parse_mode="HTML",
            reply_markup=get_reply_button(message.from_user.id)
        )

    except Exception as e:
        logging.error(e)
        await message.answer("Yuborilmadi ❌")

# =========================
# REPLY
# =========================

@dp.callback_query(F.data.startswith("reply_"))
async def reply(call: CallbackQuery, state: FSMContext):

    target_id = int(call.data.split("_")[1])

    await state.update_data(target_id=target_id)
    await state.set_state(SearchState.chatting)

    await call.message.answer("Suhbat boshlandi 💬", reply_markup=get_active_chat_kb())
    await call.answer()

# =========================
# SERVER
# =========================

async def handle(request):
    return web.Response(text="Bot is running!")

async def main():

    await db.client.admin.command("ping")
    logging.info("MongoDB OK ✅")

    app = web.Application()
    app.router.add_get("/", handle)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)

    await site.start()

    logging.info(f"Server {port} portda ishlayapti")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
