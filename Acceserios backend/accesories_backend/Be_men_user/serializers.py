from rest_framework import serializers
from .models import User

from django.contrib.auth.password_validation import validate_password


class UserSignupSerializer(serializers.ModelSerializer):
    
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)  # confirm password

    class Meta:
        model = User
        fields = ['name', 'email', 'phone_number', 'profile_picture', 'password', 'password2']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn’t match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        return User.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            phone_number=validated_data.get('phone_number'),
            profile_picture=validated_data.get('profile_picture', 'default.png'),
            password=validated_data['password']
        )



class UserLoginSerializer(serializers.Serializer):
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)



class UserProfileSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'phone_number', 'profile_picture']
        read_only_fields = ['email']



class PasswordChangeSerializer(serializers.Serializer):
    
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    
    
