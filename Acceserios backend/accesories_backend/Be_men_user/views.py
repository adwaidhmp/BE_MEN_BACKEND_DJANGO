from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSignupSerializer, UserProfileSerializer
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.hashers import make_password


from rest_framework import generics, status
from .serializers import UserSignupSerializer

class SignupView(generics.CreateAPIView):
    
    serializer_class = UserSignupSerializer


from rest_framework.views import APIView
class LoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        user = authenticate(email=email, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            response = Response({"detail": "Login successful"}, status=status.HTTP_200_OK)

            # Set cookies (HTTP dev-friendly)
            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                secure=True,  # must be False for HTTP
                samesite="None", # works with same-origin
            )
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=True,
                samesite="None",
            )
            return response
        return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)




class ProfileView(generics.RetrieveAPIView):
    
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
    



class LogoutView(APIView):
    def post(self, request):
        response = Response({'detail': 'Logged out successfully'})
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response




class ProfileUpdateView(generics.UpdateAPIView):
    
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:
            return Response({"detail": "Both old and new password required"}, status=400)

        user = request.user
        if not user.check_password(old_password):
            return Response({"detail": "Old password incorrect"}, status=400)

        user.set_password(new_password)
        user.save()
        return Response({"detail": "Password changed successfully"})

    



from django.contrib.auth import get_user_model

User = get_user_model()  # Use your custom user model

class ForgotPasswordView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal whether the email exists for security
            return Response(
                {'message': 'If an account with this email exists, a reset link has been sent.'},
                status=status.HTTP_200_OK
            )

        # Generate password reset token
        token_generator = PasswordResetTokenGenerator()
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)

        # Construct reset URL for frontend
        reset_url = f"http://localhost:5173/reset-password/{uidb64}/{token}/"

        # Send reset email
        send_mail(
            'Reset Your Password',
            f'Click the link below to reset your password:\n{reset_url}',
            'noreply@example.com',
            [email],
            fail_silently=False,
        )

        return Response({'message': 'Password reset link sent to your email.'}, status=status.HTTP_200_OK)
    




class ResetPasswordView(APIView):
    def post(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'error': 'Invalid link'}, status=status.HTTP_400_BAD_REQUEST)

        token_generator = PasswordResetTokenGenerator()
        if not token_generator.check_token(user, token):
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)

        new_password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')

        if new_password != confirm_password:
            return Response({'error': 'Passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)

        user.password = make_password(new_password)
        user.save()

        return Response({'message': 'Password reset successfully!'}, status=status.HTTP_200_OK)


        

from rest_framework_simplejwt.tokens import RefreshToken, TokenError

class RefreshTokenView(APIView):

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response({'detail': 'Refresh token missing'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            # Verify and decode refresh token
            refresh = RefreshToken(refresh_token)
            new_access = str(refresh.access_token)

            # Create response with new access token
            response = Response({'access': new_access}, status=status.HTTP_200_OK)
            
            # Update access token cookie
            response.set_cookie(
                key="access_token",
                value=new_access,
                httponly=True,
                secure=True,       # True only in HTTPS
                samesite="None"      # "None" if cross-domain in HTTPS
            )
            return response

        except TokenError:
            return Response({'detail': 'Invalid or expired refresh token'}, status=status.HTTP_401_UNAUTHORIZED)
        
        