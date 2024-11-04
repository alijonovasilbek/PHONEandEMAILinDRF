import random
import re
from datetime import datetime, timedelta
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth import authenticate, login, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    RegisterSerializer, VerifyCodeSerializer, LoginSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer
)
from .models import User
from .eskiz_api import EskizAPI



User = get_user_model()
eskiz_api = EskizAPI() 
eskiz_api = EskizAPI()

class RegisterView(APIView):
    @swagger_auto_schema(request_body=RegisterSerializer)
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            email_or_phone = serializer.validated_data['email_or_phone']
            password = serializer.validated_data['password']
            
            # Check if a user already exists with this email or phone
            user = User.objects.filter(email_or_phone=email_or_phone).first()
            
            if user:
                if user.is_active:
                    # If the user is active, they are already registered
                    return Response({"email_or_phone": "This email or phone number is already registered."},
                                    status=status.HTTP_400_BAD_REQUEST)
                else:
                    # If the user exists but is inactive, resend the verification code
                    verification_code = random.randint(1000, 9999)
                    register_method = serializer.context.get('register_method', 'email')

                    # Resend the code based on the register method
                    if register_method == 'phone':
                        eskiz_api.send_sms(email_or_phone, f"Your verification code is {verification_code}")
                        print(verification_code)
                    else:
                        subject = 'Your Verification Code'
                        message = f'Your verification code is: {verification_code}'
                        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email_or_phone])

                    # Cache the new code
                    cache.set(
                        f'verification_code_{user.id}',
                        {'code': verification_code, 'timestamp': datetime.now().timestamp(), 'method': register_method},
                        timeout=30  # 5 minutes
                    )

                    # Include user_id in response for existing unverified user
                    return Response({"user_id": user.id, "message": "Verification code resent"}, status=status.HTTP_200_OK)

            # No user exists, proceed with creating a new one
            verification_code = random.randint(1000, 9999)
            register_method = serializer.context.get('register_method', 'email')

            # Send the code
            if register_method == 'phone':
                eskiz_api.send_sms(email_or_phone, f"Your verification code is {verification_code}")
                print(verification_code)
            else:
                subject = 'Your Verification Code'
                message = f'Your verification code is: {verification_code}'
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email_or_phone])

            # Create and save the new user
            user = serializer.save()
            cache.set(
                f'verification_code_{user.id}',
                {'code': verification_code, 'timestamp': datetime.now().timestamp(), 'method': register_method},
                timeout=30  # 5 minutes
            )
            user.is_active = False
            user.save()

            # Include user_id in response for new user registration
            return Response({"user_id": user.id, "message": "Verification code sent"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class LoginView(APIView):
    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email_or_phone = serializer.validated_data['email_or_phone']
            password = serializer.validated_data['password']
            user = authenticate(request, email_or_phone=email_or_phone, password=password)
            
            if user is not None:
                
                login(request, user)
                
                
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    "message": "Login successful",
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }, status=status.HTTP_200_OK)
            
            return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyCodeView(APIView):
    @swagger_auto_schema(request_body=VerifyCodeSerializer)
    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            entered_code = serializer.validated_data['code']

            try:
                user = User.objects.get(id=user_id)
                cached_data = cache.get(f'verification_code_{user.id}')

                if cached_data:
                    verification_code = cached_data['code']
                    timestamp = cached_data['timestamp']

                    if str(verification_code) == str(entered_code) and datetime.now() - datetime.fromtimestamp(timestamp) < timedelta(minutes=5):
                        user.is_active = True
                        user.save()
                        cache.delete(f'verification_code_{user.id}')
                        return Response({"message": "Verification successful"}, status=status.HTTP_200_OK)
                    return Response({"error": "Verification code expired or invalid"}, status=status.HTTP_400_BAD_REQUEST)
                return Response({"error": "Verification code expired or does not exist"}, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





class ForgotPasswordView(APIView):
    @swagger_auto_schema(request_body=ForgotPasswordSerializer)
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email_or_phone = serializer.validated_data['email_or_phone']
            user = User.objects.filter(email_or_phone=email_or_phone).first()
            
            if user:
                verification_code = random.randint(1000, 9999)
                print(verification_code)
                
                
                cache.set(f'verification_code_{user.id}', verification_code, timeout=60)
                
               
                if re.match(r'^\+998\d{9}$', email_or_phone): 
                    self.send_sms(email_or_phone, verification_code)
                    print(verification_code)
                    message = "Verification code sent to your phone."
                
                else:
                   
                    subject = "Your Password Reset Verification Code"
                    message = f"Your password reset verification code is {verification_code}."
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email_or_phone])
                    message = "Verification code sent to your email."
                
                return Response({"message": message}, status=status.HTTP_200_OK)
            
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def send_sms(self, phone, verification_code):
        """
        Sends SMS containing verification code to the user's phone.
        You can replace this method's implementation with actual SMS API integration.
        """
        
        try:
            eskiz_api.send_sms(phone, f"Your password reset verification code is {verification_code}")
        except Exception as e:
            print(f"Failed to send SMS: {e}")


class ResetPasswordView(APIView):
    @swagger_auto_schema(request_body=ResetPasswordSerializer)
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email_or_phone = serializer.validated_data['email_or_phone']
            verification_code = serializer.validated_data['verification_code']
            new_password = serializer.validated_data['new_password']
            
            user = User.objects.filter(email_or_phone=email_or_phone).first()
            if user:
                cached_code = cache.get(f'verification_code_{user.id}')
                if cached_code and str(cached_code) == str(verification_code):
                    user.set_password(new_password)
                    user.save()
                    cache.delete(f'verification_code_{user.id}')
                    return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)
                return Response({"error": "Invalid or expired verification code."}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
