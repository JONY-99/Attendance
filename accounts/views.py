from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from django.utils.timezone import now
from datetime import timedelta
import random
import uuid
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from accounts.sms import send_otp_to_telegram
from .models import UserModel, OTPmodel
from .serializers import RegisterSerializer, OTPSerializer, LoginSerializer, ResendOTPSerializer




def create_otp():
    return str(random.choice([random.randint(1000, 9999), random.randint(100000, 999999)]))

def limit_otp(user):
    last_hours = now() - timedelta(hours=2)
    count = OTPmodel.objects.filter(user=user, created_at__gte=last_hours).count()
    return count >= 3

@swagger_auto_schema(
    method='post',
    operation_summary="Foydalanuvchini ro‘yxatdan o‘tkazish",
    request_body=RegisterSerializer,
    responses={
        201: openapi.Response(description="OTP yuborildi"),
        400: "Xatolik yuz berdi"
    }
)
@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    data = request.data
    phone = data.get("phone")

    # Telefon raqam bo‘yicha foydalanuvchini tekshiramiz
    existing_user = UserModel.objects.filter(phone=phone).first()

    if existing_user:
        if existing_user.is_verify:
            return Response({"error": "User allaqachon mavjud va tasdiqlangan"}, status=status.HTTP_400_BAD_REQUEST)
        # Bu user hali verify qilinmagan – unga OTP qayta yuboramiz
        if limit_otp(existing_user):
            return Response({"error": "2 soatda 3 martadan ortiq OTP so'raldi"}, status=status.HTTP_400_BAD_REQUEST)

        otp_code = create_otp()
        otp_key = str(uuid.uuid4())
        OTPmodel.objects.create(
            user=existing_user,
            otp_code=otp_code,
            otp_key=otp_key,
            expires_at=now() + timedelta(minutes=2)
        )
        
        send_otp_to_telegram(phone_number=existing_user.phone, otp_code=otp_code)

        return Response({"otp_key": otp_key}, status=status.HTTP_201_CREATED)

    # Agar umuman user yo‘q bo‘lsa, ro‘yxatdan o‘tkazamiz
    serializer = RegisterSerializer(data=data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = serializer.save()
    otp_code = create_otp()
    otp_key = str(uuid.uuid4())
    OTPmodel.objects.create(
        user=user,
        otp_code=otp_code,
        otp_key=otp_key,
        expires_at=now() + timedelta(minutes=2)
    )
    
    send_otp_to_telegram(phone_number=user.phone, otp_code=otp_code)

    return Response({"otp_key": otp_key}, status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    method='post',
    operation_summary="OTP ni tasdiqlash",
    request_body=OTPSerializer,
    responses={
        200: openapi.Response(description="User tasdiqlandi"),
        400: "Noto‘g‘ri OTP yoki eskirgan"
    }
)
@api_view(["POST"])
@permission_classes([AllowAny])
def verify_otp(request):
    

    serializer = OTPSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    otp = OTPmodel.objects.filter(otp_key=serializer.validated_data["otp_key"]).first()
    if not otp:
        return Response({"error": "OTP topilmadi"}, status=status.HTTP_400_BAD_REQUEST)
    
    if otp.expires_at <= now():
        return Response({"error": "OTP muddati tugagan"}, status=status.HTTP_400_BAD_REQUEST)

    user = otp.user
    if user.failed_attempts >= 2:
        return Response({"error": "Ko'p noto'g'ri urinishlar. Keyinroq urinib ko'ring"}, status=status.HTTP_400_BAD_REQUEST)

    if otp.otp_code != serializer.validated_data["otp_code"]:
        user.failed_attempts += 1
        user.save()
        return Response({"error": "Noto'g'ri OTP"}, status=status.HTTP_400_BAD_REQUEST)

    user.is_verify = True
    user.failed_attempts = 0
    user.save()
    otp.delete()
    refresh = RefreshToken.for_user(user)
    return Response({
        "message": "Foydalanuvchi tasdiqlandi",
         
    })

resend_otp_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['otp_key'],
    properties={
        'otp_key': openapi.Schema(type=openapi.TYPE_STRING, format="uuid")
    }
)

@swagger_auto_schema(
    method='post',
    operation_summary="OTP qayta yuborish",
    request_body=ResendOTPSerializer,
    responses={
        201: openapi.Response(description="Yangi OTP yuborildi"),
        400: "Xatolik"
    }
)
@api_view(["POST"])
@permission_classes([AllowAny])
def resend_otp(request):
    
    otp_key = request.data.get("otp_key")

    otp = OTPmodel.objects.filter(otp_key=otp_key, expires_at__gt=now()).first()
    if not otp:
        return Response({"error": "OTP topilmadi yoki eskirgan"}, status=status.HTTP_400_BAD_REQUEST)

    user = otp.user
    if limit_otp(user):
        return Response({"error": "Cheklov: 2 soatda 3 martadan ortiq"}, status=status.HTTP_400_BAD_REQUEST)

    OTPmodel.objects.filter(user=user).delete()
    otp_code = create_otp()
    otp_key_new = str(uuid.uuid4())
    OTPmodel.objects.create(user=user, otp_code=otp_code, otp_key=otp_key_new, expires_at=now() + timedelta(minutes=2))
    print(otp_code)
    send_otp_to_telegram(phone_number=user.phone, otp_code=otp_code)
    return Response({"otp_key": otp_key_new}, status=status.HTTP_201_CREATED)

login_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['phone', 'password'],
    properties={
        'phone': openapi.Schema(type=openapi.TYPE_STRING),
        'password': openapi.Schema(type=openapi.TYPE_STRING, format='password')
    }
)

@swagger_auto_schema(
    method='post',
    operation_summary="Login qilish",
    request_body=LoginSerializer,
    responses={
        200: openapi.Response(description="Tokenlar qaytdi"),
        400: "Login xatolik"
    }
)
@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    ...

    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response({"error": "username va parol talab qilinadi"}, status=status.HTTP_400_BAD_REQUEST)

    user = UserModel.objects.filter(username=username).first()
    if not user or not user.check_password(password):
        return Response({"error": "username yoki parol noto‘g‘ri"}, status=status.HTTP_400_BAD_REQUEST)

    refresh = RefreshToken.for_user(user)
    return Response({
        "access_token": str(refresh.access_token),
        "refresh_token": str(refresh)
    })

@swagger_auto_schema(
    method='post',
    operation_summary="Logout qilish",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['refresh_token'],
        properties={
            'refresh_token': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={
        200: openapi.Response(description="Logout muvaffaqiyatli"),
        400: "Xatolik"
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    """
    Logout view to blacklist the refresh token.
    """
    try:
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response({"error": "Refresh token talab qilinadi"}, status=status.HTTP_400_BAD_REQUEST)

        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Logout muvaffaqiyatli"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
@swagger_auto_schema(
    method='post',
    operation_summary="Parolni unutganlar uchun",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['phone'],
        properties={
            'phone': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={
        200: openapi.Response(description="OTP yuborildi"),
        400: "Xatolik",
        404: "Foydalanuvchi topilmadi"
    }
)
@api_view(["POST"])
@permission_classes([AllowAny])
def forgot_password(request):
    """
    Forgot password view to send OTP for password reset.
    """
    
    phone = request.data.get("phone")
    if not phone:
        return Response({"error": "Telefon raqami talab qilinadi"}, status=status.HTTP_400_BAD_REQUEST)

    user = UserModel.objects.filter(phone=phone).first()
    if not user:
        return Response({"error": "Foydalanuvchi topilmadi"}, status=status.HTTP_404_NOT_FOUND)

    otp_code = create_otp()
    otp_key = str(uuid.uuid4())
    OTPmodel.objects.create(
        user=user,
        otp_code=otp_code,
        otp_key=otp_key,
        expires_at=now() + timedelta(minutes=2)
    )
    
    send_otp_to_telegram(phone_number=user.phone, otp_code=otp_code)

    return Response({"otp_key": otp_key}, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='post',
    operation_summary="Parolni yangilash",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['otp_key', 'otp_code', 'new_password'],
        properties={
            'otp_key': openapi.Schema(type=openapi.TYPE_STRING, format="uuid"),
            'otp_code': openapi.Schema(type=openapi.TYPE_STRING),
            'new_password': openapi.Schema(type=openapi.TYPE_STRING, format='password')
        }
    ),
    responses={
        200: openapi.Response(description="Parol muvaffaqiyatli yangilandi"),
        400: "Xatolik"
    }
)
@api_view(["POST"])
@permission_classes([AllowAny])
def update_password(request):
    """
    Update password view to change the user's password.
    """
    otp_key = request.data.get("otp_key")
    otp_code = request.data.get("otp_code")
    new_password = request.data.get("new_password")

    if not otp_key or not otp_code or not new_password:
        return Response({"error": "OTP kaliti, OTP kodi va yangi parol talab qilinadi"}, status=status.HTTP_400_BAD_REQUEST)    
    
    otp = OTPmodel.objects.filter(otp_key=otp_key, expires_at__gt=now()).first()
    if not otp:
        return Response({"error": "OTP topilmadi yoki eskirgan"}, status=status.HTTP_400_BAD_REQUEST)
    
    if otp.otp_code != otp_code:
        return Response({"error": "Noto‘g‘ri OTP kodi"}, status=status.HTTP_400_BAD_REQUEST)
    
    user = otp.user
    user.set_password(new_password)
    user.save()
    otp.delete()

    return Response({"message": "Parol muvaffaqiyatli yangilandi"}, status=status.HTTP_200_OK)





