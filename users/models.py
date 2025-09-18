from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
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
    phone_number = models.CharField(max_length=10, unique=True, null=True, blank=True,validators=[RegexValidator(r'^\d{10}$', 'Phone number must be exactly 10 digits.')])
    national_id = models.CharField(max_length=10, null=True, blank=True,validators=[RegexValidator(r'^\d{10}$', 'National ID must be 8 digits.')])
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    image = models.ImageField(upload_to='profile_images/', default=None)
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
class ArtisanPortfolio(models.Model):
    artisan = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'user_type': 'artisan'})
    title = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.title

class PortfolioImage(models.Model):
    portfolio = models.ForeignKey(ArtisanPortfolio, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='portfolio_images/', default=None)
    def __str__(self):
        return f"Image for {self.portfolio.title}"