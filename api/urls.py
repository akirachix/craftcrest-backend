from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserRegistrationView, LoginView, ForgotPasswordView,
    OTPVerificationView, PasswordResetView,
    AdminListUsersView, UserViewSet, ArtisanPortfolioViewSet
)

artisan_portfolio_list = ArtisanPortfolioViewSet.as_view({'get': 'list', 'post': 'create'})
artisan_portfolio_detail = ArtisanPortfolioViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})

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
    path('artisan-portfolio/', artisan_portfolio_list, name='artisan-portfolio-list'),
]