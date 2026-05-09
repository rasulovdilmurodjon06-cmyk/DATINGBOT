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
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.db import Database
import config

# =========================
# CONFIG
# =========================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# config.py ichida bo'lishi kerak:
# API_TOKEN = "TOKEN"
# MONGO_URI = "mongodb+srv://..."
# ADMIN_IDS = [123456789]  # admin Telegram ID lari
# REGIONS = ["Toshkent", "Samarqand", ...]

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

class AdminState(StatesGroup):
    menu = State()
    broadcast = State()
    ban_user = State()
    unban_user = State()

# =========================
# KEYBOARDS
# =========================

def get_main_menu():
    kb = [
        [
            KeyboardButton(text="Qidiruv 🔍"),
            KeyboardButton(text="Profilim 👤")
        ],
        [
            KeyboardButton(text="Sozlamalar ⚙️")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_profile_kb():
    kb = [
        [KeyboardButton(text="Profilni tahrirlash 📝")],
        [KeyboardButton(text="Orqaga ⬅️")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_edit_fields_kb():
    kb = [
        [
            KeyboardButton(text="Ismni o'zgartirish"),
            KeyboardButton(text="Yoshni o'zgartirish")
        ],
        [
            KeyboardButton(text="Viloyatni o'zgartirish"),
            KeyboardButton(text="Rasmni o'zgartirish")
        ],
        [
            KeyboardButton(text="Orqaga ⬅️")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_regions_kb():
    buttons = [KeyboardButton(text=r) for r in config.REGIONS]
    kb = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    kb.append([KeyboardButton(text="Orqaga ⬅️")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_search_kb():
    kb = [
        [
            KeyboardButton(text="Yigit topish 🧒"),
            KeyboardButton(text="Qiz topish 🧕")
        ],
        [
            KeyboardButton(text="Orqaga ⬅️")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_chat_kb():
    kb = [
        [
            KeyboardButton(text="Xabar yuborish ✉️"),
            KeyboardButton(text="Keyingisi ⏭")
        ],
        [
            KeyboardButton(text="Orqaga ⬅️")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_active_chat_kb():
    kb = [
        [
            KeyboardButton(text="Suhbatni yakunlash ❌")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_reply_button(target_id):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Javob berish ✍️",
        callback_data=f"reply_{target_id}"
    )
    return builder.as_markup()

def get_admin_menu_kb():
    kb = [
        [
            KeyboardButton(text="📊 Statistika"),
            KeyboardButton(text="📢 Xabar yuborish")
        ],
        [
            KeyboardButton(text="🚫 Foydalanuvchini bloklash"),
            KeyboardButton(text="✅ Blokdan chiqarish")
        ],
        [
            KeyboardButton(text="👥 Foydalanuvchilar ro'yxati"),
            KeyboardButton(text="🔙 Chiqish")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# =========================
# HELPERS
# =========================

def is_admin(user_id: int) -> bool:
    return user_id in getattr(config, "ADMIN_IDS", [])

# =========================
# START
# =========================

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):

    await state.clear()

    user = await db.get_user(message.from_user.id)

    if not user:
        kb = [
            [
                KeyboardButton(text="O'zbekcha 🇺🇿"),
                KeyboardButton(text="English 🇺🇸")
            ]
        ]
        await message.answer(
            "Assalomu alaykum!\nBotga xush kelibsiz.\nTilni tanlang:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=kb,
                resize_keyboard=True
            )
        )
        await state.set_state(Registration.language)
    else:
        await message.answer(
            "Xush kelibsiz!",
            reply_markup=get_main_menu()
        )

# =========================
# ADMIN PANEL
# =========================

@dp.message(Command("admin"))
async def admin_panel(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ Sizda admin huquqi yo'q.")

    await state.clear()
    await state.set_state(AdminState.menu)

    await message.answer(
        "👨‍💼 <b>Admin panel</b>\n\nXush kelibsiz, admin!",
        parse_mode="HTML",
        reply_markup=get_admin_menu_kb()
    )

@dp.message(AdminState.menu, F.text == "📊 Statistika")
async def admin_stats(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    try:
        total_users = await db.get_users_count()
        active_users = await db.get_active_users_count()
        banned_users = await db.get_banned_users_count()

        text = (
            "📊 <b>Bot statistikasi</b>\n\n"
            f"👥 Jami foydalanuvchilar: <b>{total_users}</b>\n"
            f"✅ Faol foydalanuvchilar: <b>{active_users}</b>\n"
            f"🚫 Bloklangan foydalanuvchilar: <b>{banned_users}</b>"
        )
    except Exception as e:
        logging.error(f"Stats error: {e}")
        text = "❌ Statistikani olishda xatolik yuz berdi."

    await message.answer(text, parse_mode="HTML")

@dp.message(AdminState.menu, F.text == "👥 Foydalanuvchilar ro'yxati")
async def admin_users_list(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    try:
        users = await db.get_all_users(limit=20)

        if not users:
            return await message.answer("Foydalanuvchilar topilmadi.")

        text = "👥 <b>So'nggi 20 foydalanuvchi:</b>\n\n"
        for u in users:
            uid = u.get("user_id", "?")
            name = u.get("full_name", "Nomsiz")
            age = u.get("age", "?")
            region = u.get("region", "?")
            banned = "🚫" if u.get("is_banned") else "✅"
            text += f"{banned} <b>{name}</b> | {age} yosh | {region} | ID: <code>{uid}</code>\n"

    except Exception as e:
        logging.error(f"Users list error: {e}")
        text = "❌ Foydalanuvchilar ro'yxatini olishda xatolik."

    await message.answer(text, parse_mode="HTML")

@dp.message(AdminState.menu, F.text == "📢 Xabar yuborish")
async def admin_broadcast_start(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "📢 Barcha foydalanuvchilarga yuboriladigan xabarni kiriting:\n\n"
        "(Bekor qilish uchun /cancel)",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(AdminState.broadcast)

@dp.message(AdminState.broadcast)
async def admin_broadcast_send(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    if message.text == "/cancel":
        await state.set_state(AdminState.menu)
        return await message.answer(
            "Bekor qilindi.",
            reply_markup=get_admin_menu_kb()
        )

    try:
        users = await db.get_all_users()
        sent = 0
        failed = 0

        for user in users:
            try:
                await bot.send_message(
                    user["user_id"],
                    f"📢 <b>Admin xabari:</b>\n\n{message.text}",
                    parse_mode="HTML"
                )
                sent += 1
                await asyncio.sleep(0.05)
            except Exception:
                failed += 1

        await message.answer(
            f"✅ Xabar yuborildi!\n\n"
            f"✔️ Muvaffaqiyatli: {sent}\n"
            f"❌ Yuborilmadi: {failed}",
            reply_markup=get_admin_menu_kb()
        )

    except Exception as e:
        logging.error(f"Broadcast error: {e}")
        await message.answer(
            "❌ Xabar yuborishda xatolik yuz berdi.",
            reply_markup=get_admin_menu_kb()
        )

    await state.set_state(AdminState.menu)

@dp.message(AdminState.menu, F.text == "🚫 Foydalanuvchini bloklash")
async def admin_ban_start(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "🚫 Bloklash uchun foydalanuvchi ID sini kiriting:\n\n"
        "(Bekor qilish uchun /cancel)",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(AdminState.ban_user)

@dp.message(AdminState.ban_user)
async def admin_ban_execute(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    if message.text == "/cancel":
        await state.set_state(AdminState.menu)
        return await message.answer(
            "Bekor qilindi.",
            reply_markup=get_admin_menu_kb()
        )

    if not message.text or not message.text.strip().lstrip("-").isdigit():
        return await message.answer(
            "❌ Noto'g'ri ID. Raqam kiriting:"
        )

    target_id = int(message.text.strip())

    try:
        user = await db.get_user(target_id)

        if not user:
            await message.answer(
                "❌ Bunday foydalanuvchi topilmadi.",
                reply_markup=get_admin_menu_kb()
            )
        else:
            await db.ban_user(target_id)
            await message.answer(
                f"✅ Foydalanuvchi <code>{target_id}</code> bloklandi.",
                parse_mode="HTML",
                reply_markup=get_admin_menu_kb()
            )
            try:
                await bot.send_message(
                    target_id,
                    "🚫 Siz botdan bloklangansiz."
                )
            except Exception:
                pass

    except Exception as e:
        logging.error(f"Ban error: {e}")
        await message.answer(
            "❌ Bloklashda xatolik yuz berdi.",
            reply_markup=get_admin_menu_kb()
        )

    await state.set_state(AdminState.menu)

@dp.message(AdminState.menu, F.text == "✅ Blokdan chiqarish")
async def admin_unban_start(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "✅ Blokdan chiqarish uchun foydalanuvchi ID sini kiriting:\n\n"
        "(Bekor qilish uchun /cancel)",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(AdminState.unban_user)

@dp.message(AdminState.unban_user)
async def admin_unban_execute(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    if message.text == "/cancel":
        await state.set_state(AdminState.menu)
        return await message.answer(
            "Bekor qilindi.",
            reply_markup=get_admin_menu_kb()
        )

    if not message.text or not message.text.strip().lstrip("-").isdigit():
        return await message.answer(
            "❌ Noto'g'ri ID. Raqam kiriting:"
        )

    target_id = int(message.text.strip())

    try:
        user = await db.get_user(target_id)

        if not user:
            await message.answer(
                "❌ Bunday foydalanuvchi topilmadi.",
                reply_markup=get_admin_menu_kb()
            )
        else:
            await db.unban_user(target_id)
            await message.answer(
                f"✅ Foydalanuvchi <code>{target_id}</code> blokdan chiqarildi.",
                parse_mode="HTML",
                reply_markup=get_admin_menu_kb()
            )
            try:
                await bot.send_message(
                    target_id,
                    "✅ Siz botdan blokdan chiqarildingiz. /start bosing."
                )
            except Exception:
                pass

    except Exception as e:
        logging.error(f"Unban error: {e}")
        await message.answer(
            "❌ Blokdan chiqarishda xatolik yuz berdi.",
            reply_markup=get_admin_menu_kb()
        )

    await state.set_state(AdminState.menu)

@dp.message(AdminState.menu, F.text == "🔙 Chiqish")
async def admin_exit(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.clear()
    await message.answer(
        "Admin paneldan chiqildi.",
        reply_markup=get_main_menu()
    )

# =========================
# BACK
# =========================

@dp.message(F.text == "Orqaga ⬅️")
async def go_back(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Asosiy menyu:",
        reply_markup=get_main_menu()
    )

# =========================
# END CHAT
# =========================

@dp.message(F.text == "Suhbatni yakunlash ❌")
async def end_chat(message: types.Message, state: FSMContext):

    data = await state.get_data()
    target_id = data.get("target_id")

    if target_id:
        try:
            await bot.send_message(
                target_id,
                "Suhbatdosh suhbatni yakunladi ❌",
                reply_markup=get_main_menu()
            )
        except Exception as e:
            logging.error(e)

    await state.clear()
    await message.answer(
        "Suhbat yakunlandi.",
        reply_markup=get_main_menu()
    )

# =========================
# REGISTRATION
# =========================

@dp.message(Registration.language)
async def set_lang(message: types.Message, state: FSMContext):

    lang = "uz" if "O'zbekcha" in message.text else "en"

    await db.add_user(
        message.from_user.id,
        message.from_user.username,
        lang
    )

    await message.answer("Ismingizni kiriting:")
    await state.set_state(Registration.name)

@dp.message(Registration.name)
async def set_name(message: types.Message, state: FSMContext):

    if not message.text or not message.text.strip():
        return await message.answer("Iltimos, ismingizni kiriting:")

    await db.update_user(
        message.from_user.id,
        full_name=message.text.strip()
    )

    await message.answer("Yoshingizni kiriting:")
    await state.set_state(Registration.age)

@dp.message(Registration.age)
async def set_age(message: types.Message, state: FSMContext):

    if not message.text or not message.text.isdigit() or not 10 <= int(message.text) <= 80:
        return await message.answer(
            "Yoshni to'g'ri kiriting (10-80 oralig'ida):"
        )

    await db.update_user(
        message.from_user.id,
        age=int(message.text)
    )

    kb = [
        [
            KeyboardButton(text="Yigit 🧒"),
            KeyboardButton(text="Qiz 🧕")
        ]
    ]

    await message.answer(
        "Jinsingizni tanlang:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=kb,
            resize_keyboard=True
        )
    )
    await state.set_state(Registration.gender)

@dp.message(Registration.gender)
async def set_gender(message: types.Message, state: FSMContext):

    if not message.text or ("Yigit" not in message.text and "Qiz" not in message.text):
        return await message.answer("Iltimos, tugmadan tanlang:")

    gender = "male" if "Yigit" in message.text else "female"

    await db.update_user(
        message.from_user.id,
        gender=gender
    )

    await message.answer(
        "Viloyatingizni tanlang:",
        reply_markup=get_regions_kb()
    )
    await state.set_state(Registration.region)

@dp.message(Registration.region)
async def set_region(message: types.Message, state: FSMContext):

    if message.text == "Orqaga ⬅️":
        return await go_back(message, state)

    if message.text not in config.REGIONS:
        return await message.answer(
            "Iltimos, ro'yxatdan viloyat tanlang:",
            reply_markup=get_regions_kb()
        )

    await db.update_user(
        message.from_user.id,
        region=message.text
    )

    await message.answer(
        "Profil rasmingizni yuboring 📸",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Registration.photo)

@dp.message(Registration.photo, F.photo)
async def set_photo(message: types.Message, state: FSMContext):

    await db.update_user(
        message.from_user.id,
        photo=message.photo[-1].file_id
    )

    await message.answer(
        "Ro'yxatdan o'tish tugadi ✅",
        reply_markup=get_main_menu()
    )
    await state.clear()

@dp.message(Registration.photo)
async def photo_required(message: types.Message):
    await message.answer("Iltimos rasm yuboring 📸")

# =========================
# PROFILE
# =========================

@dp.message(F.text == "Profilim 👤")
async def my_profile(message: types.Message):

    user = await db.get_user(message.from_user.id)

    if not user:
        return await message.answer(
            "Profil topilmadi.\n/start bosing."
        )

    caption = (
        f"👤 Ism: {user.get('full_name', 'Kiritilmagan')}\n"
        f"🔢 Yosh: {user.get('age', 'Kiritilmagan')}\n"
        f"⚥ Jins: {'Yigit 🧒' if user.get('gender') == 'male' else 'Qiz 🧕' if user.get('gender') == 'female' else 'Kiritilmagan'}\n"
        f"📍 Viloyat: {user.get('region', 'Kiritilmagan')}"
    )

    if user.get("photo"):
        await message.answer_photo(
            user["photo"],
            caption=caption,
            reply_markup=get_profile_kb()
        )
    else:
        await message.answer(
            caption,
            reply_markup=get_profile_kb()
        )

# =========================
# SETTINGS
# =========================

@dp.message(F.text == "Sozlamalar ⚙️")
async def settings_menu(message: types.Message):
    await message.answer(
        "Sozlamalar:",
        reply_markup=get_profile_kb()
    )

# =========================
# EDIT PROFILE
# =========================

@dp.message(F.text == "Profilni tahrirlash 📝")
async def edit_profile(message: types.Message, state: FSMContext):
    await message.answer(
        "Nimani o'zgartiramiz?",
        reply_markup=get_edit_fields_kb()
    )
    await state.set_state(EditProfile.choosing_field)

@dp.message(EditProfile.choosing_field)
async def choose_field(message: types.Message, state: FSMContext):

    if not message.text:
        return

    if "Ism" in message.text:
        await message.answer("Yangi ism:")
        await state.update_data(field="full_name")

    elif "Yosh" in message.text:
        await message.answer("Yangi yosh:")
        await state.update_data(field="age")

    elif "Viloyat" in message.text:
        await message.answer(
            "Yangi viloyat:",
            reply_markup=get_regions_kb()
        )
        await state.update_data(field="region")

    elif "Rasm" in message.text:
        await message.answer("Yangi rasm yuboring:")
        await state.update_data(field="photo")

    elif "Orqaga" in message.text:
        return await go_back(message, state)

    else:
        return

    await state.set_state(EditProfile.updating_value)

@dp.message(EditProfile.updating_value)
async def update_value(message: types.Message, sta
