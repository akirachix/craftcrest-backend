from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from cart.models import ShoppingCart, CartItem
from .serializers import ShoppingCartSerializer, CartItemSerializer,InventorySerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from products.models import Inventory
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model



User = get_user_model()

class ShoppingCartViewSet(viewsets.ModelViewSet):
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        carts = self.queryset
        serializer = self.get_serializer(carts, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save()

    def update(self, request, *args, **kwargs):
        partial = False
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        partial = True
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()

    def delete_cart(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_delete(self, instance):
        instance.delete()





class CartItemViewSet(viewsets.ViewSet):

    def create(self, request):
        user = request.user
        if isinstance(user, str):
            user = User.objects.get(username=user)
        cart, _ = ShoppingCart.objects.get_or_create(user=user)
        serializer = CartItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(cart=cart)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        user = request.user
        if isinstance(user, str):
            user = User.objects.get(username=user)
        cart_item = get_object_or_404(CartItem, pk=pk, cart__user=user)
        serializer = CartItemSerializer(cart_item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete_cart_item(self, request, pk=None):
        user = request.user
        if isinstance(user, str):
            user = User.objects.get(username=user)
        cart_item = get_object_or_404(CartItem, pk=pk, cart__user=user)
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        artisan_id = self.request.query_params.get('artisan_id')
        if artisan_id:
            return self.queryset.filter(artisan_id=artisan_id)
        return self.queryset

