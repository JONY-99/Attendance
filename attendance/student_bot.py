import os
import logging
import asyncio
import requests
from urllib.parse import urljoin
from PIL import Image
from pyzbar.pyzbar import decode

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties

from .utils import get_token

# Logging sozlamasi
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Konfiguratsiya
BOT_TOKEN = "8171545298:AAGuK0udKrMTp51ibJ_cynHZeEWOa0gFCik"
API_URL = "http://localhost:8000/api/lessons"

# Bot va Dispatcher
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# /start komandasi
@dp.message(Command("start"))
async def start_handler(message: Message):
    logging.info(f"/start komandasi: {message.from_user.id}")
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True
    )
    await message.answer("Assalomu alaykum!\nIltimos, telefon raqamingizni yuboring 👇", reply_markup=keyboard)

# Telefon raqam yuborilishi
@dp.message(lambda msg: msg.contact is not None)
async def contact_handler(message: Message):
    logging.info(f"Kontakt yuborildi: {message.contact.phone_number}")
    await message.answer(
        f"✅ Qabul qilindi:\n📞 {message.contact.phone_number}\n🆔 {message.from_user.id}\n👤 {message.from_user.full_name}",
        reply_markup=ReplyKeyboardRemove()
    )

# QR olish komandasi
@dp.message(Command("get_qr"))
async def student_qr(message: Message):
    jwt_token = get_token(message.from_user.id)
    if not jwt_token:
        await message.answer("❌ Avval /login orqali tizimga kiring.")
        return

    try:
        res = requests.get(f"{API_URL}/student_active_lesson/", headers={"Authorization": jwt_token})
        data = res.json()
        if res.status_code != 200 or not data:
            await message.answer("❗️Siz uchun hozircha aktiv dars yo‘q.")
            return

        qr_url = data.get("qr_code_url")
        if qr_url.startswith("/"):
            qr_url = urljoin(API_URL, qr_url)

        await message.answer_photo(FSInputFile.from_url(qr_url), caption="📷 QR kodni skaner qiling.")
    except Exception as e:
        logging.error(f"QR olishda xatolik: {e}")
        await message.answer("❌ QR olishda xatolik yuz berdi.")

# QR yuborilgan rasmni o‘qish
@dp.message(lambda msg: msg.photo)
async def qr_handler(message: Message):
    file = await bot.get_file(message.photo[-1].file_id)
    file_path = f"qr_images/{message.from_user.id}.png"
    os.makedirs("qr_images", exist_ok=True)
    jwt_token = get_token(message.from_user.id)

    await bot.download_file(file.file_path, destination=file_path)
    logging.info(f"QR rasm saqlandi: {file_path}")

    image = Image.open(file_path)
    decoded = decode(image)

    if not decoded:
        logging.warning("QR kod o‘qilmadi.")
        await message.answer("❌ QR o‘qib bo‘lmadi.")
        return

    uuid = decoded[0].data.decode("utf-8")
    logging.info(f"QR dan o‘qilgan UUID: {uuid}")

    try:
        response = requests.post(
            f"{API_URL}/uuid/{uuid}/mark_attendance/",
            headers={"Authorization": jwt_token}
        )
        if response.status_code == 201:
            await message.answer("✅ Davomat belgilandi.")
        else:
            logging.warning(f"Davomat belgilanmadi: {response.json()}")
            await message.answer(f"⚠️ Belgilanmadi: {response.json().get('detail')}")
    except Exception as e:
        logging.error(f"Davomat belgilashda xatolik: {e}")
        await message.answer(f"❌ Xatolik: {str(e)}")

# Admin tomonidan QR'larni o‘quvchilarga yuborish
@dp.message(Command("check_qr"))
async def notify_students(message: Message):
    logging.info("Admin QR jo‘natmoqda...")
    try:
        res = requests.post("http://127.0.0.1:8000/notify_lesson_students/", json={"lesson_id": 5})
        if res.status_code != 200:
            await message.answer("❌ Xatolik yuz berdi.")
            return

        for student in res.json():
            try:
                await bot.send_photo(
                    chat_id=student["telegram_id"],
                    photo=f"http://127.0.0.1:8000{student['qr_code']}",
                    caption=f"📚 Dars boshlandi: <b>{student['subject']}</b>",
                    parse_mode="HTML"
                )
                logging.info(f"QR yuborildi: {student['telegram_id']}")
            except Exception as e:
                logging.error(f"[XATO] {student['telegram_id']} ga yuborilmadi: {e}")

        await message.answer("✅ O‘quvchilarga yuborildi.")
    except Exception as e:
        logging.error(f"QR yuborishda xatolik: {e}")
        await message.answer("❌ Jo‘natishda xatolik yuz berdi.")

# Asosiy ishga tushirish
async def main():
    logging.info("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
