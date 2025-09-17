from django.db import models
from users.models import User
from products.models import Inventory
class ShoppingCart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,limit_choices_to={'user_type': 'artisan'})
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    added_at = models.DateTimeField(auto_now_add=True)