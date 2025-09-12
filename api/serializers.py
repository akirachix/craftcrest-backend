from .daraja import DarajaAPI
from payments.models import Payment
from rest_framework import serializers

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class STKPushSerializer(serializers.Serializer):
    buyer_phone = serializers.CharField(max_length=15)
    artisan_phone = serializers.CharField(max_length=15)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = serializers.CharField(max_length=100)
    transaction_desc = serializers.CharField(max_length=255)