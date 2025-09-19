
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from .utils import haversine
from users.models import User, ArtisanPortfolio, ArtisanProfile
from api.serializers import UserSerializer, NearbyArtisanSearchSerializer
import logging

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from .serializers import (
    STKPushSerializer,
    PaymentSerializer,
    DeliveryConfirmSerializer,
    RefundSerializer,
    B2CPaymentSerializer,
    OrderSerializer, RatingSerializer,
    OrderStatusSerializer, CustomDesignRequestSerializer,ShoppingCartSerializer, ItemSerializer
)
from payments.models import Payment
from orders.models import Order
from django.utils import timezone
import datetime
from .daraja import DarajaAPI
from rest_framework.permissions import IsAuthenticated
from .serializers import ShoppingCartSerializer,InventorySerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from products.models import Inventory
from cart.models import ShoppingCart, Item
from django.shortcuts import render
from rest_framework.exceptions import PermissionDenied
from orders.models import Order, Rating, OrderStatus, CustomDesignRequest

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


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

class STKPushView(APIView):
    def post(self, request):
        serializer = STKPushSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            daraja = DarajaAPI()
            try:
                response = daraja.stk_push(
                    buyer_phone=data["buyer_phone"],
                    amount=data["amount"],
                    transaction_id=data["transaction_code"],
                    transaction_desc=data["transaction_desc"],
                )
                checkout_request_id = response.get('CheckoutRequestID', None)
                if checkout_request_id:
                    order = data['order_obj']
                    artisan = data['artisan_obj']
                    Payment.objects.create(
                        order=order,
                        artisan=artisan,
                        amount=data['amount'],
                        transaction_code=data['transaction_code'],
                        status='held',
                        paid_at=timezone.now(),
                        # held_by_platform defaults to True
                    )
                    return Response(response, status=status.HTTP_200_OK)
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response(
                    {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def daraja_callback(request):
    callback_data = request.data
    try:
        stk_callback = callback_data['Body']['stkCallback']
        checkout_request_id = stk_callback['CheckoutRequestID']
        result_code = stk_callback['ResultCode']
        result_desc = stk_callback['ResultDesc']
        payment = Payment.objects.get(transaction_code=checkout_request_id)
        if result_code == 0:
            payment.status = 'held'
            items = stk_callback.get('CallbackMetadata', {}).get('Item', [])
            item_dict = {item['Name']: item.get('Value') for item in items}
            payment.amount = item_dict.get('Amount', payment.amount)
            payment.paid_at = timezone.now()
            payment.save()
        elif result_code == 1:
            payment.status = 'refunded'
            payment.save()
    except Payment.DoesNotExist:
        pass
    except Exception:
        pass
    return Response({"status": "callback processed"})

class DeliveryConfirmView(APIView):
    def post(self, request):
        serializer = DeliveryConfirmSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            try:
                order = Order.objects.get(id=data['order_id'])
                payment = Payment.objects.get(order=order)
                if order.delivery_confirmed:
                    return Response({"detail": "Already confirmed."}, status=400)
                order.delivery_confirmed = True
                order.status = 'completed'
                order.save()
                daraja = DarajaAPI()
                response = daraja.b2c_payment(
                    artisan_phone=order.artisan.phone_number,
                    amount=payment.amount,
                    transaction_id=payment.transaction_code,
                    transaction_desc="Delivery confirmed"
                )
                payment.status = "released"
                payment.released_at = timezone.now()
                payment.held_by_platform = False
                payment.save()
                return Response(
                    {
                        "detail": "Delivery confirmed and payout released.",
                        "b2c_response": response,
                    }
                )
            except Exception as e:
                return Response(
                    {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RefundPaymentView(APIView):
    def post(self, request):
        serializer = RefundSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            try:
                order = Order.objects.get(id=data['order_id'])
                payment = Payment.objects.get(order=order)
                payment.status = "refunded"
                # Add a refund reason field to Payment model if you want to store this
                payment.held_by_platform = False
                payment.released_at = timezone.now()
                payment.save()
                return Response({"detail": "Refund processed."})
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def auto_release_payments():
    now = timezone.now()
    payments = Payment.objects.filter(status="held")
    for payment in payments:
        order = payment.order
        if hasattr(order, 'delivery_confirmed') and order.delivery_confirmed:
            continue
        if payment.paid_at and (now - payment.paid_at).total_seconds() > 86400:
            daraja = DarajaAPI()
            try:
                response = daraja.b2c_payment(
                    artisan_phone=order.artisan.phone_number,
                    amount=payment.amount,
                    transaction_id=payment.transaction_code,
                    transaction_desc="Auto-release after 24hr"
                )
                payment.status = "released"
                payment.released_at = now
                payment.held_by_platform = False
                payment.save()
            except Exception:
                continue

class B2CPaymentView(APIView):
    def post(self, request):
        serializer = B2CPaymentSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            daraja = DarajaAPI()
            try:
                response = daraja.b2c_payment(
                    artisan_phone=data["artisan_phone"],
                    amount=data["amount"],
                    transaction_id=data["transaction_id"],
                    transaction_desc=data.get("transaction_desc", ""),
                    occassion=data.get("occassion", ""),
                )
                return Response(response, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

