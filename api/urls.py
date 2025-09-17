from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ShoppingCartViewSet,InventoryViewSet
from api.views import (
    OrderViewSet, RatingViewSet,
    OrderStatusViewSet, CustomDesignRequestViewSet
)

router = DefaultRouter()
router.register(r'carts', ShoppingCartViewSet, basename='cart')
router.register(r'inventory', InventoryViewSet, basename='inventory')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'ratings', RatingViewSet, basename='rating')
router.register(r'trackings', OrderStatusViewSet, basename='orderstatus')
router.register(r'custom-requests', CustomDesignRequestViewSet, basename='customdesignrequest')

urlpatterns = [
    path('api/', include(router.urls)),
]







