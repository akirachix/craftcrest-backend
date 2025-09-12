from django.db import models

class Payment(models.Model):
    STATUS_CHOICES = (
        ('held', 'Held'),
        ('released', 'Released'),
        ('refunded', 'Refunded'),
    )
    buyer_phone = models.CharField(max_length=15, default="UNKNOWN")
    artisan_phone = models.CharField(max_length=15, default="UNKNOWN")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='held')
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Payment {self.transaction_id} - Status: {self.status}'