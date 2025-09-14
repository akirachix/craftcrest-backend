from django.db import models
from users.models import User
from products.models import Inventory

class ShoppingCart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'buyer'})
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_items = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CartItem(models.Model):
    cart = models.ForeignKey(ShoppingCart, on_delete=models.CASCADE, related_name='items')
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_when_added = models.DecimalField(max_digits=10, decimal_places=2)  
    customizable = models.BooleanField(default=False) 
    custom_options = models.TextField(blank=True, null=True)  

    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('cart', 'inventory')
