import requests
from django.conf import settings


def send_otp_to_telegram(phone_number, otp_code):
    message = f"📲 OTP KOD: {otp_code}\n📞 Telefon: {phone_number}"
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": settings.TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=data)
