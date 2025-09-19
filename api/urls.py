from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import NearbyArtisansView, UserViewSet


router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    
    path('api/nearby-artisans/', NearbyArtisansView.as_view(), name='nearby-artisans'), 
    path('api/', include(router.urls)),
]


from .views import ShoppingCartViewSet,InventoryViewSet,ItemViewSet
from api.views import (
    OrderViewSet, RatingViewSet,
    OrderStatusViewSet, CustomDesignRequestViewSet
)


router = DefaultRouter()
router.register(r'carts', ShoppingCartViewSet, basename='cart')
router.register(r'inventory', InventoryViewSet, basename='inventory')
router.register(r'items', ItemViewSet, basename='item')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'ratings', RatingViewSet, basename='rating')
router.register(r'trackings', OrderStatusViewSet, basename='orderstatus')
router.register(r'custom-requests', CustomDesignRequestViewSet, basename='customdesignrequest')


urlpatterns = [
    path('api/', include(router.urls)),
]






