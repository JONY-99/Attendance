from django.urls import path
from .views import register, login_view, verify_otp, resend_otp

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('otp-verify/', verify_otp, name='verify-opt'),
    path('resend-otp/', resend_otp, name='resend-otp'),
]
  