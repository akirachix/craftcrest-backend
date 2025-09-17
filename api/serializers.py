from .daraja import DarajaAPI
from payments.models import Payment
from orders.models import Order
from rest_framework import serializers

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['id', 'paid_at', 'released_at', 'transaction_date']

class STKPushSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    buyer_phone = serializers.CharField(max_length=15)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    transaction_code = serializers.CharField(max_length=100)
    transaction_desc = serializers.CharField(max_length=255)

    def validate(self, data):
        order = Order.objects.get(id=data['order_id'])
        buyer = order.buyer_id
        artisan = order.artisan_id
        data['artisan_phone'] = artisan.phone_number
        if not data.get('buyer_phone'):
            data['buyer_phone'] = buyer.phone_number
        return data

class DeliveryConfirmSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()

class RefundSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    reason = serializers.CharField(max_length=255)

