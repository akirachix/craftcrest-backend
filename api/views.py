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
)
from payments.models import Payment
from orders.models import Order
from django.utils import timezone
import datetime
from .daraja import DarajaAPI

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