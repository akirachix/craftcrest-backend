from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from cart.models import ShoppingCart
from rest_framework import viewsets, permissions
from .serializers import ShoppingCartSerializer,InventorySerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from products.models import Inventory

from django.contrib.auth import get_user_model



User = get_user_model()

class ShoppingCartViewSet(viewsets.ModelViewSet):
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer
    

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'artisan':
            return ShoppingCart.objects.filter(user=user)
        return ShoppingCart.objects.none()
    
class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
   

    def get_queryset(self):
        artisan_id = self.request.query_params.get('artisan_id')
        if artisan_id:
            return self.queryset.filter(artisan_id=artisan_id)
        return self.queryset

