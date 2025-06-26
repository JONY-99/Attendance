# 📦 Importlar
import os
import json
import asyncio
import requests
from urllib.parse import urljoin
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# 🔧 Mahalliy fayldan funksiyalar
from .utils import get_attendance_stat, get_lessons_by_teacher

# 🔑 Token va API sozlamalari
API_BASE = "http://localhost:8000"
BOT_TOKEN = os.getenv("TEACHER_BOT_TOKEN") or "7577607426:AAFBVGvvEI_akbsvwD7B7dTqq9-QAC7M810"
TOKEN_FILE = "teacher_tokens.json"

# 🤖 Bot va Dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 📁 Tokenlar bilan ishlovchi yordamchi funksiyalar
def load_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_tokens(tokens):
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f)

def get_token(user_id):
    return load_tokens().get(str(user_id))

def set_token(user_id, token):
    tokens = load_tokens()
    tokens[str(user_id)] = token
    save_tokens(tokens)

# 🔐 Login uchun holatlar
class LoginState(StatesGroup):
    username = State()
    password = State()

# 📌 /start komandasi
@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(
        "👋 Assalomu alaykum, Ustoz!\n\n"
        "/login - Kirish\n"
        "/lessons - Darslar\n"
        "/stat - Statistika"
    )

# 🔐 /login komandasi (username bosqichi)
@dp.message(Command("login"))
async def login_start(message: Message, state: FSMContext):
    await message.answer("👤 Iltimos, login (username) kiriting:")
    await state.set_state(LoginState.username)

# 🔐 Parol olish
@dp.message(LoginState.username)
async def get_username(message: Message, state: FSMContext):
    await state.update_data(username=message.text)
    await message.answer("🔑 Endi parolni kiriting:")
    await state.set_state(LoginState.password)

# 🔐 Token olish
@dp.message(LoginState.password)
async def get_password(message: Message, state: FSMContext):
    data = await state.get_data()
    username = data['username']
    password = message.text

    res = requests.post(f"{API_BASE}/login/", json={"username": username, "password": password})

    if res.status_code == 200:
        token = res.json().get("access_token")
        set_token(message.from_user.id, f"Bearer {token}")
        await message.answer("✅ Muvaffaqiyatli kirdingiz!")
    else:
        await message.answer("❌ Login yoki parol noto‘g‘ri")

    await state.clear()

# 📚 /lessons komandasi
@dp.message(Command("lessons"))
async def lesson_list_handler(message: Message):
    jwt_token = get_token(message.from_user.id)
    if not jwt_token:
        await message.answer("❌ Iltimos, avval /login orqali tizimga kiring.")
        return

    lessons = get_lessons_by_teacher(jwt_token)
    if not lessons:
        await message.answer("❌ Darslar topilmadi.")
        return

    buttons = [
    [InlineKeyboardButton(
        text=f"{l['subject_name']} - {l['time']}",
        callback_data=f"lesson_{l['id']}"
    )]
    for l in lessons
]



    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("📚 Darslaringiz ro'yxati:", reply_markup=markup)


 

# Noto‘g‘ri belgilarni tozalovchi yordamchi funksiya
def safe_text(text):
    return text.encode("utf-8", "replace").decode("utf-8")

@dp.callback_query(F.data.startswith("lesson_"))
async def lesson_selected(callback: CallbackQuery):
    user_id = callback.from_user.id
    jwt_token = get_token(user_id)

    if not jwt_token:
        await callback.message.answer("❌ Avval /login orqali tizimga kiring.")
        return

    lesson_id = int(callback.data.split("_")[1])

    try:
        # 1. Dars ma'lumotlari
        lesson_res = requests.get(
            f"{API_BASE}/teacher_lessons/?lesson_id={lesson_id}",
            headers={"Authorization": jwt_token}
        )
        if lesson_res.status_code == 401:
            await callback.message.answer("❗ Token muddati tugagan. Iltimos, qaytadan /login qiling.")
            return
        if lesson_res.status_code != 200 or not lesson_res.json():
            await callback.message.answer("❌ Dars topilmadi.")
            return

        lesson_data = lesson_res.json()[0]
        subject_name = lesson_data.get("subject_name", "Noma'lum fan")
        qr_code_path = lesson_data.get("qr_code", "")
        qr_url = urljoin(API_BASE, qr_code_path)

        # 2. O‘quvchilarni olish
        student_res = requests.get(
            f"{API_BASE}/lesson_students/?lesson_id={lesson_id}",
            headers={"Authorization": jwt_token}
        )
        if student_res.status_code != 200:
            await callback.message.answer("❌ O‘quvchilarni olishda xatolik.")
            return

        students = student_res.json().get("students", [])
        caption = safe_text(
            f"📢 <b>Dars boshlandi:</b> {subject_name}\n"
            f"⏰ QR kodni skaner qilib davomatingizni belgilang."
        )

        # 3. QR kodni har bir o‘quvchiga yuborish
        # 3. Matnni har bir o‘quvchiga yuborish (QRsiz test)
        for student in students:
            telegram_id = student.get("telegram_id")
            if telegram_id:
                try:
                    await bot.send_message(
                        chat_id=telegram_id,
                        text=caption,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    print(f"[XATO] {telegram_id} ga yuborib bo‘lmadi: {e}")


        await callback.message.answer("✅ Dars boshlandi va barcha o‘quvchilarga yuborildi.")

    except Exception as e:
        print(f"[CALLBACK ERROR] {e}")
        await callback.message.answer("⚠️ Darsni boshlashda xatolik yuz berdi.")



# 📊 /stat komandasi
@dp.message(Command("stat"))
async def stat_handler(message: Message):
    jwt_token = get_token(message.from_user.id)
    if not jwt_token:
        await message.answer("❌ Iltimos, avval /login orqali tizimga kiring.")
        return

    stats = get_attendance_stat(message.from_user.id)
    if not stats:
        await message.answer("📭 Hech qanday dars topilmadi.")
        return

    msg = "📊 <b>Statistika:</b>\n\n"
    for s in stats:
        msg += (
            f"📘 <b>{s['topic']}</b>\n"
            f"✅ Keldi: {s['present']}\n"
            f"⏱ Kechikdi: {s['late']}\n"
            f"❌ Kelmadi: {s['absent']}\n\n"
        )

    await message.answer(msg, parse_mode="HTML")

# 🚀 Botni ishga tushirish
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
