from django.db import models
from django.conf import settings
import requests
class User(models.Model):
    ARTISAN = 'artisan'
    BUYER = 'buyer'
    USER_TYPE_CHOICES = [
        (ARTISAN, 'Artisan'),
        (BUYER, 'Buyer'),
    ]
    user_id = models.AutoField(primary_key=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default=BUYER)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=254, unique=True)
    phone_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    national_id = models.CharField(max_length=10)
    image_url = models.URLField(max_length=255, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    def save(self, *args, **kwargs):
        if self.user_type == self.ARTISAN and self.address:
            lat, lon = self.get_lat_lon_from_address(self.address)
            if lat and lon:
                self.latitude = lat
                self.longitude = lon
        super().save(*args, **kwargs)
    def get_lat_lon_from_address(self, address):
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
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
        except Exception as e:
            print(f"Error fetching location: {e}")
        return None, None
    def set_location_from_address(self, address):
        if not address:
            self.location = None
            return
        url = "https://us1.locationiq.com/v1/search"
        params = {
            'key': settings.LOCATIONIQ_API_KEY,
            'q': address,
            'format': 'json',
            'limit': 1,
            'normalizeaddress': 1,
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if data:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                self.location = Point(lon, lat, srid=4326)
            else:
                self.location = None
        except Exception as e:
            print(f"Geocoding failed for {address}: {e}")
            self.location = None
            
class ArtisanPortfolio(models.Model):
    portfolio_id = models.AutoField(primary_key=True)
    artisan_id = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'artisan'})
    image_urls = models.JSONField(default=list, blank=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.title