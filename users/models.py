import requests
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils import timezone
import random
import logging

logger = logging.getLogger(__name__)

class User(AbstractUser):
    ARTISAN = 'artisan'
    BUYER = 'buyer'
    USER_TYPE_CHOICES = [
        (ARTISAN, 'Artisan'),
        (BUYER, 'Buyer'),
    ]
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default=BUYER
    )
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=10, unique=True, null=True, blank=True, validators=[RegexValidator(r'^\d{10}$', 'Phone number must be exactly 10 digits.')])
    national_id = models.CharField(max_length=10, null=True, blank=True, validators=[RegexValidator(r'^\d{8}$', 'National ID must be 8 digits.')])
    image = models.ImageField(upload_to='profile_images/', default=None)
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_exp = models.DateTimeField(null=True, blank=True)
    otp_verified = models.BooleanField(default=False)
    username = None
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "phone_number"]

    def __str__(self):
        return f"{self.first_name or ''} {self.last_name or ''} ({self.email})".strip()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def get_lat_lon_from_address(self, address):
        if not address:
            logger.warning("No address provided for geocoding")
            return None, None
        LOCATIONIQ_API_KEY = settings.LOCATIONIQ_API_KEY
        url = "https://us1.locationiq.com/v1/search.php"
        params = {
            'key': LOCATIONIQ_API_KEY,
            'q': address,
            'format': 'json',
            'limit': 1
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data and len(data) > 0:
                lat, lon = float(data[0]['lat']), float(data[0]['lon'])
                logger.info(f"Geocoded address {address} to lat: {lat}, lon: {lon}")
                return lat, lon
            logger.warning(f"No geocoding results for address: {address}")
            return None, None
        except requests.RequestException as e:
            logger.error(f"Geocoding failed for address {address}: {e}")
            return None, None

    def generate_otp(self):
        self.otp = str(random.randint(100000, 999999))
        self.otp_exp = timezone.now() + timedelta(minutes=10)
        self.otp_verified = False
        self.save()

    def verify_otp(self, otp_value):
        if self.otp == otp_value and self.otp_exp and timezone.now() <= self.otp_exp:
            self.otp_verified = True
            self.save()
            return True
        return False

class ArtisanProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='artisanprofile',
        limit_choices_to={'user_type': 'artisan'}
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

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='profile_images/', default=None)

    def __str__(self):
        return f"{self.user.email} Profile"

class ArtisanPortfolio(models.Model):
    artisan = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'user_type': 'ARTISAN'})
    title = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def clean(self):
        if self.artisan.user_type != "ARTISAN":
            raise ValidationError("Portfolio can only be linked to an artisan user.")

    @property
    def image_urls(self):
        return [img.image.url for img in self.images.all()]

class PortfolioImage(models.Model):
    portfolio = models.ForeignKey(ArtisanPortfolio, on_delete=models.CASCADE, related_name='images', null=True, blank=True)
    image = models.ImageField(upload_to='portfolio_images/', default=None)

    def __str__(self):
        return f"Image for {self.portfolio.title}"