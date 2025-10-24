from Be_men_user.models import User
from rest_framework import serializers


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "email",
            "phone_number",
            "profile_picture",
            "is_active",
            "is_banned",
            "date_joined",
        ]
