from rest_framework import serializers
from django.conf import settings
from orders.models import Order, Rating, OrderTracking, CustomDesignRequest


from rest_framework import serializers
from orders.models import Order

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'

    def validate_order_type(self, value):
        if value not in ['ready-made', 'custom']:
            raise serializers.ValidationError("Invalid order_type")
        return value

    def validate(self, value):
        status = value.get('status')
        payment_status = value.get('payment_status')
        order_type = value.get('order_type')

        if status == 'confirmed' and payment_status != 'completed':
            raise serializers.ValidationError(
                "Payment must be completed if order status is confirmed."
            )

        if status == 'rejected':
            if not value.get('rejected_reason') or not value.get('rejected_date'):
                raise serializers.ValidationError(
                    "Rejected orders must have reason and date."
                )

        return value


class RatingSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)

    class Meta:
        model = Rating
        fields = '__all__'
        read_only_fields = ['rating_id', 'created_at']

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

class OrderTrackingSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)

    class Meta:
        model = OrderTracking
        fields = '__all__'
        read_only_fields = ['tracking_id', 'update_timestamp', 'created_at', 'approval_timestamp']

class CustomDesignRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomDesignRequest
        fields = '__all__'
        read_only_fields = ['request_id', 'created_at']