from django.db import models
from users.models import User
from orders.models import Order
class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    artisan = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'artisan'})
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_code = models.CharField(max_length=50)
    status = models.CharField(max_length=20)
    paid_at = models.DateTimeField()
    released_at = models.DateTimeField(null=True, blank=True)
    held_by_platform = models.BooleanField(default=True)

