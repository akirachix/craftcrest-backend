from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PaymentViewSet,
    daraja_callback,
    STKPushView,
    DeliveryConfirmView,
    RefundPaymentView
)

router = DefaultRouter()
router.register(r'payment', PaymentViewSet, basename='payment')

urlpatterns = [
    path("", include(router.urls)), 
    path('daraja/stk-push/', STKPushView.as_view(), name='daraja-stk-push'),
    path('daraja/callback/', daraja_callback, name='daraja-callback'),
    path('delivery/confirm/', DeliveryConfirmView.as_view(), name='delivery-confirm'),
    path('payment/refund/', RefundPaymentView.as_view(), name='payment-refund'),
]