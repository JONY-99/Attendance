# 📚 QR Code Based Attendance System

QR asosida yaratilgan o‘quvchilar uchun **davomat nazorati tizimi**. 
Tizim orqali o‘qituvchi dars boshlanishida QR kod yuboradi, o‘quvchilar uni skanerlab darsga qatnashganini tasdiqlaydi.
 Barchasi **JWT, Telegram bot** va **Swagger API** asosida ishlaydi.

---

## 🚀 Texnologiyalar

- **Python 3.10+**
- **Django & DRF (Django Rest Framework)**
- **SimpleJWT (tokenlar uchun)**
- **Swagger (drf_yasg) – test va dokumentatsiya**
- **Aiogram 3 – Telegram botlar**
- **Pillow & qrcode – QR kod generatsiyasi**
- **PostgreSQL / SQLite – Ma'lumotlar bazasi**

---

## ⚙️ Arxitektura

attendance/ → Lesson, Attendance, QR kodlar
accounts/ → UserModel, OTP modeli, Auth funksiyalar
bots/
├─ student_bot.py → O‘quvchi uchun Telegram bot
└─ teacher_bot.py → O‘qituvchi uchun Telegram bot
utils.py → QR kod generatsiyasi funksiyasi




---

## 🔐 Avtorizatsiya

- ✅ Ro‘yxatdan o‘tish (`/register/`)
- 🔐 OTP orqali tasdiqlash (`/verify/`)
- 🔁 OTP qayta yuborish (`/resend/`)
- 🔓 Login qilish (`/login/`)
- 🔑 JWT access/refresh tokenlar

---

## 👩‍🏫 O‘qituvchi Imkoniyatlari

- Dars yaratish
- QR kod generatsiya qilish
- O‘quvchilarga QR kod yuborish
- Har bir darsga oid statistikani ko‘rish

---

## 👨‍🎓 O‘quvchi Imkoniyatlari

- QR kodni skanerlab qatnashuvni belgilash
- Haftalik qatnashuv statistikasini ko‘rish
- O‘zining darsga qatnashganlarini ko‘rish

---

## 🔗 Muhim API Endpoints

| Method | Endpoint                             | Tavsifi                        |
|--------|--------------------------------------|--------------------------------|
| POST   | `/api/register/`                     | Ro‘yxatdan o‘tish              |
| POST   | `/api/verify/`                       | OTP orqali tasdiqlash          |
| POST   | `/api/login/`                        | JWT token olish                |
| GET    | `/api/lessons/`                      | Barcha darslar ro‘yxati        |
| POST   | `/api/lessons/{id}/mark_attendance/` | QR orqali qatnashuvni belgilash|
| GET    | `/api/teacher_lessons/`              | O‘qituvchining darslari        |
| GET    | `/api/my_attendance/`                | O‘quvchining qatnashuvi        |
| GET    | `/api/statistics/weekly/`            | 7 kunlik qatnashuv statistikasi|

---

## 🤖 Telegram Botlar

### 1. `student_bot.py`

- QR kodni qabul qilish
- QR koddan ma'lumotni o‘qib API orqali qatnashuvni belgilash
- Statistikani ko‘rish

### 2. `teacher_bot.py`

- Dars boshlashni bosish
- QR generatsiya qilish
- O‘quvchilarga QRni yuborish

**Telegram ID** avtomatik aniqlanadi: `message.from_user.id` orqali.

---

## ⚙️ Ishga Tushirish Qo‘llanmasi

```bash
# 1. Virtual muhit yaratish
python -m venv venv
source venv/bin/activate

# 2. Talablarni o‘rnatish
pip install -r requirements.txt

# 3. Migratsiyalar
python manage.py makemigrations
python manage.py migrate

# 4. Superuser yaratish
python manage.py createsuperuser

# 5. Django serverni ishga tushurish
python manage.py runserver

# 6. Telegram botlarni alohida terminalda ishga tushurish
python bots/student_bot.py
python bots/teacher_bot.py
