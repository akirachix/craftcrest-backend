
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from django.db.models import F, FloatField
from .utils import haversine
from django.db.models.functions import ACos, Cos, Radians, Sin
from users.models import User
from api.serializers import UserSerializer, NearbyArtisanSearchSerializer


class NearbyArtisansView(APIView):
    
    def post(self, request):
        serializer = NearbyArtisanSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lat = serializer.validated_data['latitude']
        lon = serializer.validated_data['longitude']
        radius = float(serializer.validated_data.get('radius', 50))

        artisans = User.objects.filter(
            user_type='artisan',
            latitude__isnull=False,
            longitude__isnull=False,
        )
        results = []
        for artisan in artisans:
            dist = haversine(lat, lon, artisan.latitude, artisan.longitude)
            if dist <= radius:
                portfolios = ArtisanPortfolio.objects.filter(artisan_id=artisan.user_id)
                portfolio_data = [
                    {
                        "title": p.title,
                        "description": p.description,
                        "image_urls": p.image_urls
                    } for p in portfolios
                ]
                results.append({
                    "artisan_id": artisan.user_id,
                    "first_name": artisan.first_name,
                    "last_name": artisan.last_name,
                    "distance_km": round(dist, 2),
                    "latitude": artisan.latitude,
                    "longitude": artisan.longitude,
                    "portfolio": portfolio_data,
                })

        results = sorted(results, key=lambda x: x['distance_km'])
        return Response({"artisans": results})



class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer