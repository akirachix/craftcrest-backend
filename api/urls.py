from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import (
    OrderViewSet, RatingViewSet,
    OrderStatusViewSet, CustomDesignRequestViewSet
)

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'ratings', RatingViewSet, basename='rating')
router.register(r'trackings', OrderStatusViewSet, basename='orderstatus')
router.register(r'custom-requests', CustomDesignRequestViewSet, basename='customdesignrequest')

urlpatterns = [
    path('api/', include(router.urls)),
]