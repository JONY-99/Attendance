from django.urls import path
from .views import register, login_view, verify_otp, resend_otp, logout_view, forgot_password, update_password

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('otp-verify/', verify_otp, name='verify-opt'),
    path('resend-otp/', resend_otp, name='resend-otp'),
    path('logout/', logout_view, name='logout'),
    path('forgot-password/', forgot_password, name='forgot-password'),
    path('update-password/', update_password, name='update-password'),
]
  