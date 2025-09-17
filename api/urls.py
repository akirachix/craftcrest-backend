from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ShoppingCartViewSet,InventoryViewSet

router = DefaultRouter()
router.register(r'carts', ShoppingCartViewSet, basename='cart')
router.register(r'inventory', InventoryViewSet, basename='inventory')

urlpatterns = [
    path('api/', include(router.urls)),
]
