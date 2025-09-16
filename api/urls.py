from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserRegistrationView, LoginView, ForgotPasswordView,
    OTPVerificationView, PasswordResetView,
    AdminListUsersView, UserViewSet, ArtisanPortfolioViewSet, UserProfileView
)


router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'portfolio', ArtisanPortfolioViewSet, basename='portfolio')


urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('verify-otp/', OTPVerificationView.as_view(), name='verify-otp'),
    path('reset-password/', PasswordResetView.as_view(), name='reset-password'),
    path('admin/users/', AdminListUsersView.as_view(), name='admin-list-users'),
    path('profile/',UserProfileView.as_view(), name = 'user-profile')
]