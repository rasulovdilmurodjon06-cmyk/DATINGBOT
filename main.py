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

MONGO_URI = "mongodb+srv://Dimajon:DD1559831DD@cluster0.dty9eag.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
db = Database(MONGO_URI)

PREMIUM_MARK = "⭐️"

class Registration(StatesGroup):
    language, name, age, gender, region, photo = State(), State(), State(), State(), State(), State()

class EditProfile(StatesGroup):
    choosing_field, updating_value = State(), State()

class SearchState(StatesGroup):
    browsing, chatting = State(), State()

# --- Klaviaturalar ---
def get_lang_kb():
    return types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="O'zbekcha 🇺🇿"),
                   types.KeyboardButton(text="Русский 🇷🇺"),
                   types.KeyboardButton(text="English 🇺🇸")]],
        resize_keyboard=True
    )

def get_main_menu():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Qidiruv 🔍"), types.KeyboardButton(text="Profilim 👤")],
            [types.KeyboardButton(text="Sozlamalar ⚙️")]
        ],
        resize_keyboard=True
    )

def get_search_menu_kb():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Yigit topish 🧒"), types.KeyboardButton(text="Qiz topish 🧕")],
            [types.KeyboardButton(text="Orqaga ⬅️")]
        ],
        resize_keyboard=True
    )

def get_profile_kb():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Profilni tahrirlash 📝")],
            [types.KeyboardButton(text="Orqaga ⬅️")]
        ],
        resize_keyboard=True
    )

def get_edit_fields_kb():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Ismni o'zgartirish"), types.KeyboardButton(text="Yoshni o'zgartirish")],
            [types.KeyboardButton(text="Viloyatni o'zgartirish"), types.KeyboardButton(text="Rasmni o'zgartirish")],
            [types.KeyboardButton(text="Jinsni o'zgartirish"), types.KeyboardButton(text="Tilni o'zgartirish")],
            [types.KeyboardButton(text="Orqaga ⬅️")]
        ],
        resize_keyboard=True
    )

def get_regions_kb():
    buttons = [types.KeyboardButton(text=r) for r in config.REGIONS]
    kb = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    kb.append([types.KeyboardButton(text="Orqaga ⬅️")])
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_gender_kb():
    return types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="Yigit 🧒"), types.KeyboardButton(text="Qiz 🧕")]],
        resize_keyboard=True
    )

def get_chat_kb():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Xabar yuborish ✉️"), types.KeyboardButton(text="Keyingisi ⏭")],
            [types.KeyboardButton(text="Orqaga ⬅️")]
        ],
        resize_keyboard=True
    )

def get_active_chat_kb():
    return types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="Suhbatni yakunlash ❌")]],
        resize_keyboard=True
    )

def get_reply_button(target_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="Javob berish ✍️", callback_data=f"reply_{target_id}")
    return builder.as_markup()

# --- START ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Tilni tanlang:", reply_markup=get_lang_kb())
        await state.set_state(Registration.language)
    else:
        await message.answer(f"Xush kelibsiz, {user.get('full_name')} {PREMIUM_MARK}!", reply_markup=get_main_menu())

# --- CHAT ---
@dp.message(SearchState.chatting)
async def chatting_handler(message: types.Message, state: FSMContext):
    if message.text == "Suhbatni yakunlash ❌":
        await state.clear()
        return await message.answer("Suhbat tugadi.", reply_markup=get_main_menu())

    # 🔥 TO‘G‘RILANGAN LINK FILTER
    if message.text and any(x in message.text.lower() for x in ['t.me', 'http', '@']):
        await message.delete()
        return await message.answer("Link taqiqlangan! 🚫")

    data = await state.get_data()
    target_id = data.get('target_id')

    if data.get('is_fake'):
        await asyncio.sleep(1)
        await message.answer(random.choice(["Salom!", "Qayerdansiz?", "😊"]))
    else:
        try:
            sender = await db.get_user(message.from_user.id)
            await bot.send_message(
                target_id,
                f"{sender['full_name']}: {message.text}"
            )
        except:
            await message.answer("Xabar yuborilmadi.")

# --- WEB SERVER ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)

    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 10000))).start()

    await dp.start_polling(bot)

# 🔥 ENG MUHIM TUZATISH
if __name__ == '__main__':
    asyncio.run(main())
