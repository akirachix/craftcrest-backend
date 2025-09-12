from django.db import models

class User(models.Model):
    ARTISAN = 'artisan'
    BUYER = 'buyer'
    USER_TYPE_CHOICES = [
        (ARTISAN, 'Artisan'),
        (BUYER, 'Buyer'),
    ]
    user_id = models.AutoField(primary_key=True)
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default=BUYER
    ) 
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=254, unique=True)
    phone_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    national_id = models.CharField(max_length=10)
    image_url = models.URLField(max_length=255,null=True,blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

class ArtisanPortfolio(models.Model):
    portfolio_id = models.AutoField(primary_key=True)
    artisan_id = models.ForeignKey(User, on_delete=models.CASCADE,limit_choices_to={'user_type': 'artisan'})
    image_urls = models.JSONField(default=list, blank=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title