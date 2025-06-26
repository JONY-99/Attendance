from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
import uuid

class CustomUserManager(BaseUserManager):
    def create_user(self, phone, username, telegram_id, password=None):
        if not phone:
            raise ValueError('Foydalanuvchi raqami kerak')
        user = self.model(phone=phone, username=username, telegram_id=telegram_id)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, username, telegram_id ,password=None):
        user = self.create_user(phone, username, telegram_id ,password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class  UserModel(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('1', 'Student'),
        ('2', 'Teacher'),
        ('3', 'Staff')
    )

    username = models.CharField(max_length=64)
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=32)
    password = models.CharField(max_length=128)
    phone = models.CharField(max_length=15, unique=True)
    telegram_id = models.CharField(max_length=100)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=1)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verify = models.BooleanField(default=False)
    failed_attempts = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    objects = CustomUserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['username', 'telegram_id']

    def __str__(self):
        return f"{self.username} ({self.role})"
    

class OTPmodel(models.Model):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    otp_key = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    expires_at = models.DateTimeField()
    

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"OTP for {self.user.username} - {self.otp_code}"
    
    class Meta:
        verbose_name = "OTP"
        verbose_name_plural = "OTPs"