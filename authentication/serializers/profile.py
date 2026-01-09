
from rest_framework import serializers

from ..models import Profile


# serializers/profile.py
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["id", "role", "is_profile_complete", "is_admin_approved"]
