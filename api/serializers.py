from rest_framework import serializers
from users.models import User, ArtisanProfile
from django.conf import settings
import requests
from products.models import Inventory
from cart.models import ShoppingCart , Item
from django.conf import settings
from orders.models import Order, Rating, OrderStatus, CustomDesignRequest
from orders.models import Order

from .daraja import DarajaAPI
from payments.models import Payment
from orders.models import Order
from rest_framework import serializers
class UserSerializer(serializers.ModelSerializer):
    latitude = serializers.DecimalField(source='artisanprofile.latitude', max_digits=9, decimal_places=6, read_only=True)
    longitude = serializers.DecimalField(source='artisanprofile.longitude', max_digits=9, decimal_places=6, read_only=True)
    address = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'id', 'user_type', 'first_name', 'last_name', 'email', 'phone_number',
            'national_id', 'image', 'otp_verified', 'otp_exp',
            'address', 'latitude', 'longitude',
        ]
        read_only_fields = ['otp_verified', 'otp_exp']

    def create(self, validated_data):
        address = validated_data.pop('address', None)
        user = User.objects.create(**validated_data)

        if address:
            lat, lon = self.geocode_address(address)
            if lat is not None and lon is not None:
                profile, _ = ArtisanProfile.objects.get_or_create(user=user)
                profile.latitude = lat
                profile.longitude = lon
                profile.save()

        return user


    def update(self, instance, validated_data):
        address = validated_data.pop('address', None)
        instance = super().update(instance, validated_data)

        if address:
            lat, lon = self.geocode_address(address)
            if lat is not None and lon is not None:
                profile, _ = ArtisanProfile.objects.get_or_create(user=instance)
                profile.latitude = lat
                profile.longitude = lon
                profile.save()

        return instance

    def geocode_address(self, address):
        if not address:
            return None, None
        LOCATIONIQ_API_KEY = settings.LOCATIONIQ_API_KEY
        url = "https://us1.locationiq.com/v1/search.php"
        params = {
            'key': LOCATIONIQ_API_KEY,
            'q': address,
            'format': 'json',
            'limit': 1,
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
        except requests.RequestException:
            pass
        return None, None
class NearbyArtisanSearchSerializer(serializers.Serializer):
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    radius = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, default=50)  


class ShoppingCartSerializer(serializers.ModelSerializer):
    item = serializers.PrimaryKeyRelatedField(many=True, queryset=Item.objects.all())
    class Meta:
        model = ShoppingCart
        fields = '__all__'
    def update(self, instance, validated_data):
        items = validated_data.pop('item', None)
        if items is not None:
            instance.item.set(items)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
    
class ItemSerializer (serializers.ModelSerializer):
    class Meta:
        model= Item
        fields = '__all__'       

class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = '__all__'



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

class OrderStatusSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)

    class Meta:
        model = OrderStatus
        fields = '__all__'
        read_only_fields = ['tracking_id', 'update_timestamp', 'created_at', 'approval_timestamp']

class CustomDesignRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomDesignRequest
        fields = '__all__'
        read_only_fields = ['request_id', 'created_at']




class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['id', 'paid_at', 'released_at', 'transaction_date']

class STKPushSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    buyer_phone = serializers.CharField(max_length=15, required=False)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    transaction_code = serializers.CharField(max_length=100)
    transaction_desc = serializers.CharField(max_length=255)

    def validate(self, data):
        try:
            order = Order.objects.get(id=data['order_id'])
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order does not exist")
        buyer = order.buyer
        artisan = order.artisan
        data['order_obj'] = order
        data['artisan_obj'] = artisan
        if not data.get('buyer_phone'):
            data['buyer_phone'] = buyer.phone_number
        return data

class DeliveryConfirmSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()

class RefundSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    reason = serializers.CharField(max_length=255)

class B2CPaymentSerializer(serializers.Serializer):
    artisan_phone = serializers.CharField(max_length=15)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = serializers.CharField(max_length=100)
    transaction_desc = serializers.CharField(max_length=255, required=False)
    occassion = serializers.CharField(max_length=255, required=False)

