from rest_framework import serializers
from users.models import User, ArtisanProfile
from django.conf import settings
import requests


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