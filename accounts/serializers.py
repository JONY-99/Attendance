from rest_framework import serializers
from .models import UserModel, OTPmodel
from django.contrib.auth.hashers import make_password

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = UserModel
        fields = ['username','first_name','last_name','telegram_id','phone','role','password']

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data['password'] = make_password(password)
        return UserModel.objects.create(**validated_data)


class OTPSerializer(serializers.Serializer):
    otp_key = serializers.UUIDField()
    otp_code = serializers.CharField(max_length=6)

    def validate_otp_code(self, value):

        if int(value) <= 0:
            raise serializers.ValidationError("OTP musbat son bo‘lishi kerak.")
        
        if not value.isdigit():
            raise serializers.ValidationError("OTP faqat raqamlardan iborat bo‘lishi kerak.")
        return value

class ResendOTPSerializer(serializers.Serializer):
    otp_key = serializers.CharField()
    phone = serializers.CharField()

    def validate_otp_code(self, value):

        if int(value) <= 0:
            raise serializers.ValidationError("OTP musbat son bo‘lishi kerak.")
        
        if not value.isdigit():
            raise serializers.ValidationError("OTP faqat raqamlardan iborat bo‘lishi kerak.")
         
        return value


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)



 

