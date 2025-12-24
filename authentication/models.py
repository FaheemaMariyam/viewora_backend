from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Profile(models.Model):
    ROLE_CHOICES = (
        ('client', 'client'),
        ('seller', 'seller'),
        ('broker', 'broker'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone_number = models.CharField(
        max_length=15,
        null=True,
        blank=True
    )
    is_phone_verified = models.BooleanField(default=False)

    profile_image = models.ImageField(
        upload_to="profile_images/",
        null=True,
        blank=True
    )

    is_profile_complete = models.BooleanField(default=False)
    is_admin_approved = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class BrokerDetails(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE)

    city = models.CharField(max_length=100)
    area = models.CharField(max_length=100)

    license_number = models.CharField(max_length=100)
    certificate = models.FileField(upload_to='broker_docs/')

    def __str__(self):
        return f"BrokerDetails - {self.profile.user.username}"


class SellerDetails(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE)

    city = models.CharField(max_length=100)
    area = models.CharField(max_length=100)

    ownership_proof = models.FileField(upload_to='seller_docs/')

    def __str__(self):
        return f"SellerDetails - {self.profile.user.username}"

class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10)

    def __str__(self):
        return f"OTP for {self.user.email}"

class AdminLoginOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

    def __str__(self):
        return f"Admin OTP for {self.user.username}"

class PhoneOTP(models.Model):
    phone_number = models.CharField(max_length=15)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)