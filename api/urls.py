from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import NearbyArtisansView, UserViewSet


router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    
    path('api/nearby-artisans/', NearbyArtisansView.as_view(), name='nearby-artisans'), 
    path('api/', include(router.urls)),
]