
from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated  
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from orders.models import Order, Rating, OrderStatus, CustomDesignRequest
from .serializers import (
    OrderSerializer, RatingSerializer,
    OrderStatusSerializer, CustomDesignRequestSerializer
)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer 

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'buyer_orders'):  
            return Order.objects.filter(buyer_id=user)
        elif hasattr(user, 'artisan_orders'):
            return Order.objects.filter(artisan_id=user)
        return Order.objects.none()

    def confirm_payment(self, request, pk=None):
        order = self.get_object()
        if order.payment_status != 'pending':
            raise ValidationError("Payment is not pending.")
        if self.request.user.user_type != 'buyer':
            raise PermissionDenied("Only buyers can confirm payment.")
        order.payment_status = 'completed'
        order.status = 'confirmed'
        order.save()
        return Response({"message": "Payment confirmed", "payment_status": order.payment_status})

class RatingViewSet(viewsets.ModelViewSet):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer


class OrderStatusViewSet(viewsets.ModelViewSet):
    queryset = OrderStatus.objects.all()
    serializer_class = OrderStatusSerializer

class CustomDesignRequestViewSet(viewsets.ModelViewSet):
    queryset = CustomDesignRequest.objects.all()
    serializer_class = CustomDesignRequestSerializer

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'buyer_requests'):
            return CustomDesignRequest.objects.filter(buyer_id=user)
        elif hasattr(user, 'artisan_requests'):
            return CustomDesignRequest.objects.filter(artisan_id=user)
        return CustomDesignRequest.objects.none()
    
    def perform_create(self, serializer):
        if self.request.user.user_type != 'buyer':
            raise PermissionDenied("Only buyers can create custom design requests.")
        serializer.save(buyer_id=self.request.user)

    def accept_request(self, request, pk=None):
        custom_request = self.get_object()
        if self.request.user.user_type != 'artisan':
            raise PermissionDenied("Only artisans can accept custom design requests.")
        if custom_request.artisan_id != self.request.user:
            raise PermissionDenied("You are not assigned to this request.")
        if custom_request.status != 'pending':
            raise ValidationError("Request is not pending.")
        custom_request.status = 'accepted'
        custom_request.save()
        return Response({"message": "Custom design request accepted", "status": custom_request.status})