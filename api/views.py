from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from .serializers import (
    STKPushSerializer,
    PaymentSerializer,
)
from payments.models import Payment
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
                    transaction_id=data["transaction_id"],
                    transaction_desc=data["transaction_desc"],
                )
                checkout_request_id = response.get('CheckoutRequestID', None)
                if checkout_request_id:
                    Payment.objects.create(
                        buyer_phone=data['buyer_phone'],
                        artisan_phone=data['artisan_phone'],
                        amount=data['amount'],
                        transaction_id=data['transaction_id'],
                        status='held'
                    )
                return Response(response, status=status.HTTP_200_OK)
            except Exception as e:
                return Response(
                    {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def daraja_callback(request):
    callback_data = request.data
    print("Daraja Callback Data:", callback_data)
    try:
        stk_callback = callback_data['Body']['stkCallback']
        checkout_request_id = stk_callback['CheckoutRequestID']
        result_code = stk_callback['ResultCode']
        result_desc = stk_callback['ResultDesc']
        payment = Payment.objects.get(transaction_id=checkout_request_id)
        if result_code == 0:
            payment.status = 'released'
        elif result_code == 1:
            payment.status = 'refunded'
        payment.result_description = result_desc
        if result_code == 0:
            items = stk_callback.get('CallbackMetadata', {}).get('Item', [])
            item_dict = {item['Name']: item['Value'] for item in items}
            payment.mpesa_receipt_number = item_dict.get('MpesaReceiptNumber')
            trans_date_str = str(item_dict.get('TransactionDate'))
            trans_date = datetime.datetime.strptime(trans_date_str, '%Y%m%d%H%M%S')
            payment.transaction_date = timezone.make_aware(trans_date, timezone.get_current_timezone())
            payment.amount = item_dict.get('Amount')
            payment.buyer_phone = item_dict.get('PhoneNumber')
        payment.save()
    except Payment.DoesNotExist:
        print(f"Payment with transaction_id {checkout_request_id} not found.")
    except Exception as e:
        print(f"Error processing Daraja callback: {e}")
    return Response({"status": "callback processed"})








class B2CPaymentView(APIView):
    def post(self, request):
        data = request.data
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