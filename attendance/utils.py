import requests
import json

API_BASE = "http://localhost:8000/"
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzUwNjE4MDgyLCJpYXQiOjE3NTA2MTQ0ODIsImp0aSI6IjUyZmM0MThjYjUwZDRlMGY5YmUwYTEzMjZlYzY3YzcxIiwidXNlcl9pZCI6Nn0.nIPLt-8VbL3lPHDT23diSNoTtT0OmcSSQ9VHVTlRTno"  # Hozircha test uchun qo‘lda
 
def get_lessons_by_teacher(jwt_token):
    url = f"{API_BASE}/teacher_lessons/"
    headers = {"Authorization": jwt_token}
    res = requests.get(url, headers=headers)

    if res.status_code == 200:
        return res.json()  # Bu yerda darslar listi qaytadi
    else:
        print(f"[XATO] Darslarni olishda muammo: {res.status_code} - {res.text}")
        return []


def send_qr_to_students(student_list, qr_path, caption):
    from aiogram.types import FSInputFile
    import asyncio
    from teacher_bot import bot  # Ehtiyot bo‘l — aylana import bo‘lmasin
    file = FSInputFile(qr_path)

    async def send():
        for student in student_list:
            try:
                await bot.send_photo(student["telegram_id"], photo=file, caption=caption)
            except Exception as e:
                print(f"Yuborilmadi: {student['telegram_id']} - {e}")
    asyncio.create_task(send())

def get_attendance_stat(telegram_id):
    res = requests.get(f"{API_BASE}/lessons/stat/{telegram_id}/", headers={"Authorization": f"Bearer {JWT_TOKEN}"})
    if res.status_code == 200:
        return res.json().get("data", [])
    return []



def get_jwt_token(username, password):
    url = "http://localhost:8000/login/"
    data = {
        "username": username,
        "password": password
    }
    try:
        res = requests.post(url, json=data)
        if res.status_code == 200:
            return "Bearer " + res.json()["access_token"]
        else:
            print(f"[XATO] Login muvoffaqiyatsiz: {res.status_code} - {res.text}")
            return None
    except Exception as e:
        print("[XATO] JWT olishda muammo:", e)
        return None

def get_token(user_id):
    with open("teacher_tokens.json", "r") as f:
        tokens = json.load(f)
    return tokens.get(str(user_id))