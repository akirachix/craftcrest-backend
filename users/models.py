from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from datetime import timedelta
import random

def generate_otp():
    return str(random.randint(100000, 999999))

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("user_type", "admin")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("user_type") != "admin":
            raise ValueError("Superuser must have user_type='admin'.")
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

class User(AbstractBaseUser, PermissionsMixin):
    class UserType(models.TextChoices):
        ARTISAN = "ARTISAN", "Artisan"
        BUYER = "BUYER", "Buyer"
        
    user_id = models.AutoField(primary_key=True)
    user_type = models.CharField(max_length=10, choices=UserType.choices, default=UserType.BUYER, blank=True)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(max_length=254, unique=True)
    phone_number = models.CharField(max_length=10, unique=True, null=True, blank=True,validators=[RegexValidator(r'^\d{10}$', 'Phone number must be exactly 10 digits.')])
    national_id = models.CharField(max_length=10, null=True, blank=True,validators=[RegexValidator(r'^\d{10}$', 'National ID must be 8 digits.')])
    image_url = models.URLField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_exp = models.DateTimeField(null=True, blank=True)
    otp_verified = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return f"{self.first_name or ''} {self.last_name or ''} ({self.email})".strip()

    def generate_otp(self):
        self.otp = generate_otp()
        self.otp_exp = timezone.now() + timedelta(minutes=10)
        self.otp_verified = False
        self.save()

    def verify_otp(self, otp_value):
        if self.otp == otp_value and self.otp_exp and timezone.now() <= self.otp_exp:
            self.otp_verified = True
            self.save()
            return True
        return False

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image_url = models.URLField(max_length=255, blank=True, null=True)
    def __str__(self):
        return f"{self.user.email} Profile"

class ArtisanProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'ARTISAN'}
    )
    fulfillment_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    rejection_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    days_active = models.PositiveIntegerField(default=0)
    completed_orders = models.PositiveIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    weekly_order_count = models.PositiveIntegerField(default=0)
    order_value_limit = models.DecimalField(max_digits=10, decimal_places=2, default=2000, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

    def __str__(self):
        return f"Artisan Profile for {self.user.email}"

    def clean(self):
        if self.user.user_type != 'ARTISAN':
            raise ValidationError("ArtisanProfile can only be linked to an artisan user.")

    def update_verification_status(self):
        if (
            self.fulfillment_rate >= 90
            and self.rejection_rate <= 10
            and self.average_rating >= 4.0
            and self.days_active >= 85
            and self.completed_orders >= 10
        ):
            self.is_verified = True
            self.order_value_limit = None
        else:
            self.is_verified = False
            self.order_value_limit = 2000
        self.save()

    def can_take_order(self, order_value):
        if self.is_verified:
            return True
        return order_value <= 2000 and self.weekly_order_count < 5
        
class ArtisanPortfolio(models.Model):
    portfolio_id = models.AutoField(primary_key=True)
    artisan = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'ARTISAN'}, related_name="portfolios")
    title = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    image_urls = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.title or 'Untitled'} - {self.artisan.email or self.artisan.phone_number}"

    def clean(self):
        if self.artisan.user_type != "ARTISAN":
            raise ValidationError("Portfolio can only be linked to an artisan user.")
        