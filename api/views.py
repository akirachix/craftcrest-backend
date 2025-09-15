import logging
from django.utils import timezone
from rest_framework import generics, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import NotFound
from users.models import User, ArtisanPortfolio
from users.models import Profile
import django_filters.rest_framework
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from .serializers import (
    UserRegistrationSerializer,
    LoginSerializer,
    CustomUserSerializer,
    ForgotPasswordSerializer,
    OTPVerificationSerializer,
    PasswordResetSerializer,
    ProfileSerializer,
    ArtisanPortfolioSerializer,
)
from users.permissions import AdminPermission, ArtisanPermission

logger = logging.getLogger(__name__)

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        return user


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            return Profile.objects.get(user=self.request.user)
        except Profile.DoesNotExist:
            raise NotFound("Profile not found for this user")


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        logger.debug("Login request received")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data.get('user')
        if not user:
            logger.error("Authentication returned no user.")
            return Response({"error": "User authentication failed"}, status=status.HTTP_400_BAD_REQUEST)
        token, _ = Token.objects.get_or_create(user=user)
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        user_serializer = CustomUserSerializer(user, context={'request': request})
        logger.info("Login successful for user: %s", getattr(user, 'email', 'unknown'))
        return Response({"token": token.key, "user": user_serializer.data}, status=status.HTTP_200_OK)

class ForgotPasswordView(generics.GenericAPIView):
    serializer_class = ForgotPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"success": True, "message": "OTP sent to email."}, status=status.HTTP_200_OK)

class OTPVerificationView(generics.GenericAPIView):
    serializer_class = OTPVerificationSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"success": True, "message": "OTP verified successfully."}, status=status.HTTP_200_OK)

class PasswordResetView(generics.GenericAPIView):
    serializer_class = PasswordResetSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "message": "Password reset successfully."}, status=status.HTTP_200_OK)


class AdminListUsersView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated, AdminPermission]
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['user_type'] 


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated, AdminPermission]


class ArtisanPortfolioViewSet(viewsets.ModelViewSet):
    queryset = ArtisanPortfolio.objects.all()
    serializer_class = ArtisanPortfolioSerializer
    permission_classes = [IsAuthenticated, ArtisanPermission]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return ArtisanPortfolio.objects.none()
        if user.user_type == 'ADMIN':
            return ArtisanPortfolio.objects.all()
        return ArtisanPortfolio.objects.filter(artisan=user)

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated or user.user_type != 'ARTISAN':
            raise serializers.ValidationError({"detail": "Only artisans can create portfolios."})
        serializer.save(artisan=user)








        