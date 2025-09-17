from rest_framework import serializers
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'user_id', 'user_type', 'first_name', 'last_name', 'email', 'phone_number',
            'address', 'latitude', 'longitude',
        ]
        read_only_fields = ['latitude', 'longitude']


class NearbyArtisanSearchSerializer(serializers.Serializer):
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    radius = serializers.DecimalField(max_digits=5, decimal_places=2, default=50)
