from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile
from django.contrib.auth.password_validation import validate_password

# class RegisterSerializer(serializers.ModelSerializer):
#     role = serializers.ChoiceField(choices=Profile.ROLE_CHOICES)

#     class Meta:
#         model = User
#         fields = ['username', 'email', 'password', 'role']
#         extra_kwargs = {'password': {'write_only': True}}

#     def create(self, validated_data):
#         role = validated_data.pop('role')
#         user = User.objects.create_user(**validated_data)
#         Profile.objects.create(user=user, role=role)
#         return user
class RegisterSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=Profile.ROLE_CHOICES)
    phone_number = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role', 'phone_number']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        role = validated_data.pop('role')
        phone_number = validated_data.pop('phone_number')

        user = User.objects.create_user(**validated_data)

        Profile.objects.create(
            user=user,
            role=role,
            phone_number=phone_number,
            is_phone_verified=True
        )
        return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            'id',
            'role',
            'is_profile_complete',
            'is_admin_approved',
        ]

class ChangePasswordSerializer(serializers.Serializer):
    old_password=serializers.CharField(write_only=True)
    new_password=serializers.CharField(write_only=True)

    def validate_new_password(self,value):
        validate_password(value)
        return value

class ResetPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

class AdminOTPVerifySerializer(serializers.Serializer):
    username = serializers.CharField()
    otp = serializers.CharField(max_length=6)
