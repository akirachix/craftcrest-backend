from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ShoppingCartViewSet,InventoryViewSet,ItemViewSet

router = DefaultRouter()
router.register(r'carts', ShoppingCartViewSet, basename='cart')
router.register(r'inventory', InventoryViewSet, basename='inventory')
router.register(r'items', ItemViewSet, basename='item')


urlpatterns = [
    path('api/', include(router.urls)),
]
