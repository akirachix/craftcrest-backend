from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, permissions
from .serializers import ShoppingCartSerializer,InventorySerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from products.models import Inventory

from rest_framework import viewsets, permissions
from cart.models import ShoppingCart, Item
from .serializers import ShoppingCartSerializer, ItemSerializer

class ShoppingCartViewSet(viewsets.ModelViewSet):
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer
    # permission_classes = [IsAuthenticated]

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    # permission_classes = [permissions.IsAuthenticated]

    
class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
   

    def get_queryset(self):
        artisan_id = self.request.query_params.get('artisan')
        if artisan_id:
            return self.queryset.filter(artisan_id=artisan_id)
        return self.queryset

