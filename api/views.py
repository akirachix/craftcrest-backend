from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from .utils import haversine
from users.models import User, ArtisanPortfolio, ArtisanProfile
from api.serializers import UserSerializer, NearbyArtisanSearchSerializer
import logging

logger = logging.getLogger(__name__)

class NearbyArtisansView(APIView):
    def post(self, request):
        serializer = NearbyArtisanSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lat = float(serializer.validated_data['latitude'])  
        lon = float(serializer.validated_data['longitude'])
        radius = float(serializer.validated_data.get('radius', 50))

        artisans = User.objects.filter(
            user_type='artisan',
            artisanprofile__latitude__isnull=False,
            artisanprofile__longitude__isnull=False,
        ).select_related('artisanprofile')

        results = []
        for artisan in artisans:
            try:
                artisan_profile = artisan.artisanprofile
                if artisan_profile.latitude is None or artisan_profile.longitude is None:
                    continue
                dist = haversine(lat, lon, float(artisan_profile.latitude), float(artisan_profile.longitude))
                if dist <= radius:
                    portfolios = ArtisanPortfolio.objects.filter(artisan_id=artisan.id)
                    portfolio_data = [
                        {
                            "title": p.title,
                            "description": p.description,
                            "images": p.image_urls
                        }
                        for p in portfolios
                    ]
                    results.append({
                        "id": artisan.id,
                        "first_name": artisan.first_name,
                        "last_name": artisan.last_name,
                        "distance_km": round(dist, 2),
                        "latitude": artisan_profile.latitude,
                        "longitude": artisan_profile.longitude,
                        "portfolio": portfolio_data,
                    })
            except ArtisanProfile.DoesNotExist:
                logger.warning(f"Artisan {artisan.email} has no ArtisanProfile")
                continue

        results = sorted(results, key=lambda x: x['distance_km'])
        logger.info(f"Returning {len(results)} artisans within radius")
        return Response({"artisans": results})


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer