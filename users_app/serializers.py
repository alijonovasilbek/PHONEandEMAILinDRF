from rest_framework import serializers
from .models import User
import re


class RegisterSerializer(serializers.ModelSerializer):
    email_or_phone = serializers.CharField()
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email_or_phone', 'password',
            'gender', 'age', 'height', 'weight', 'goal', 'level' 
        ]

    def validate_email_or_phone(self, value):
        # Regex to check if the input is a valid phone number or email
        phone_regex = r'^\+998\d{9}$'

        if re.match(phone_regex, value):
            self.context['register_method'] = 'phone'
            return value

        # Validate as email if not a phone number
        try:
            serializers.EmailField().run_validation(value)
            self.context['register_method'] = 'email'
            return value
        except serializers.ValidationError:
            raise serializers.ValidationError("The input must be a valid phone number starting with +998 or a valid email address.")

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class VerifyCodeSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    code = serializers.IntegerField()


class LoginSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField(max_length=255)
    password = serializers.CharField(write_only=True)


class ForgotPasswordSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField(max_length=255)




class ResetPasswordSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField(max_length=255)
    verification_code = serializers.IntegerField()
    new_password = serializers.CharField(write_only=True, max_length=128)

