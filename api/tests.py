from django.test import TestCase
from rest_framework.exceptions import ValidationError
from django.core.exceptions import PermissionDenied
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from decimal import Decimal
from datetime import datetime, timedelta
from users.models import User, ArtisanPortfolio
from products.models import Inventory
from orders.models import (
    Order, Rating, OrderTracking, CustomDesignRequest
)
from api.serializers import (
    OrderSerializer, RatingSerializer,
    OrderTrackingSerializer, CustomDesignRequestSerializer
)
from api.views import(
    CustomDesignRequestViewSet, OrderTrackingViewSet,RatingViewSet, OrderViewSet
)

class OrdersSerializersModelsTestCase(TestCase):
    def setUp(self):
        self.buyer = User.objects.create(
            user_type=User.BUYER,
            first_name="Dorothy",
            last_name="Khaenzeli",
            email="dorothy@example.com",
            phone_number="0712345678",
            national_id="1234567890"
        )
        self.artisan = User.objects.create(
            user_type=User.ARTISAN,
            first_name="Maxwell",
            last_name="David",
            email="maxwell@example.com",
            phone_number="0798765432",
            national_id="0987654321"
        )

        self.portfolio = ArtisanPortfolio.objects.create(
            artisan_id=self.artisan,
            title="Elegant Jewelry",
            description="Handcrafted jewelry pieces.",
            image_urls=["http://example.com/img1.jpg", "http://example.com/img2.jpg"]
        )


        self.order = Order.objects.create(
            buyer_id=self.buyer,
            artisan_id=self.artisan,
            order_type='ready-made',
            status='pending',
            quantity=1,
            total_amount=Decimal("100.00"),
            payment_status='pending'
        )

        self.custom_design_request = CustomDesignRequest.objects.create(
            buyer_id=self.buyer,
            artisan_id=self.artisan,
            description="Sample design",
            deadline=datetime.now().date() + timedelta(days=5),
            status='material-sourcing',
            quote_amount=Decimal("200.00"),
            material_price=Decimal("50.00"),
            labour_price=Decimal("50.00")
        )

        self.order_tracking = OrderTracking.objects.create(
            order_id=self.order,
            artisan_id=self.artisan,
            status='pending'
        )

        self.rating = Rating.objects.create(
            order_id=self.order,
            buyer_id=self.buyer,
            rating=5
        )
 
    def test_user_str_representation(self):
        self.assertEqual(str(self.buyer), "Dorothy Khaenzeli (dorothy@example.com)")
        self.assertEqual(str(self.artisan), "Maxwell David (maxwell@example.com)")

    def test_artisan_portfolio_str_representation(self):
        self.assertEqual(str(self.portfolio), "Elegant Jewelry")
        self.assertEqual(self.portfolio.artisan_id.user_type, User.ARTISAN)
        self.assertIsInstance(self.portfolio.image_urls, list)

    def test_user_email_unique_constraint(self):
        with self.assertRaises(Exception):
            User.objects.create(
                user_type=User.BUYER,
                first_name="Chebet",
                last_name="Uzed",
                email="dorothy@example.com",  
                phone_number="0799999999",
                national_id="1111111111"
            )

    def test_order_serializer_valid_order_type(self):
        serializer = OrderSerializer(instance=self.order)
        data = serializer.data
        self.assertIn(data['order_type'], ['ready-made', 'custom'])

    def test_order_serializer_invalid_order_type(self):
        data = {
            "buyer_id": self.buyer.user_id,
            "artisan_id": self.artisan.user_id,
            "order_type": 'invalid-type',
            "status": 'pending',
            "quantity": 1,
            "total_amount": "100.00",
            "payment_status": "pending"
        }
        serializer = OrderSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("order_type", serializer.errors)


    def test_order_serializer_confirmed_requires_payment_completed(self):
        data = {
            "buyer_id": self.buyer.user_id,
            "artisan_id": self.artisan.user_id,
            "order_type": 'ready-made',
            "status": 'confirmed',
            "quantity": 1,
            "total_amount": "100.00",
            "payment_status": "pending"
        }
        serializer = OrderSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        errors = serializer.errors
        self.assertTrue(
            'non_field_errors' in errors or
            'status' in errors or
            any('payment' in str(err).lower() for err in errors.values())
        )

    def test_rating_serializer_valid_rating(self):
        serializer = RatingSerializer(instance=self.rating)
        data = serializer.data
        self.assertTrue(1 <= data['rating'] <= 5)

    def test_rating_serializer_invalid_rating(self):
        data = {
            "order_id": self.order.id,
            "buyer_id": self.buyer.user_id,
            "rating": 6,
            "review_text": ""
        }
        serializer = RatingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("rating", serializer.errors)

    def test_order_tracking_serializer_fields(self):
        serializer = OrderTrackingSerializer(instance=self.order_tracking)
        data = serializer.data
        self.assertIn('created_at', data)

    def test_custom_design_request_serializer_fields(self):
        serializer = CustomDesignRequestSerializer(instance=self.custom_design_request)
        data = serializer.data
        self.assertIn('created_at', data)


    def test_confirm_payment_only_buyer_can_confirm(self):
        self.order.payment_status = 'pending'
        self.order.status = 'pending'
        self.order.save()
        view = OrderViewSet()
        view.request = type("Request", (), {})()
        view.request.user = self.buyer
        view.kwargs = {'pk': self.order.pk}
        view.get_object = lambda: self.order
        response = view.confirm_payment(view.request, pk=self.order.pk)
        self.assertEqual(response.data['payment_status'], 'completed')
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'confirmed')
        self.assertEqual(self.order.payment_status, 'completed')

    def test_custom_design_request_only_buyer_can_create(self):
        view = CustomDesignRequestViewSet()
        view.request = type("Request", (), {})()
        view.request.user = self.artisan
        serializer = CustomDesignRequestSerializer(instance=self.custom_design_request)
        with self.assertRaises(PermissionDenied):
            view.perform_create(serializer)

    def test_accept_custom_design_request_only_artisan_can_accept(self):
        self.custom_design_request.status = 'pending'
        self.custom_design_request.artisan_id = self.artisan
        self.custom_design_request.save()
        view = CustomDesignRequestViewSet()
        view.request = type("Request", (), {})()
        view.request.user = self.buyer
        view.kwargs = {'pk': self.custom_design_request.pk}
        view.get_object = lambda: self.custom_design_request
        with self.assertRaises(PermissionDenied):
            view.accept_request(view.request, pk=self.custom_design_request.pk)

    def test_accept_custom_design_request_artisan_accepts(self):
        self.custom_design_request.status = 'pending'
        self.custom_design_request.artisan_id = self.artisan
        self.custom_design_request.save()
        view = CustomDesignRequestViewSet()
        view.request = type("Request", (), {})()
        view.request.user = self.artisan
        view.kwargs = {'pk': self.custom_design_request.pk}
        view.get_object = lambda: self.custom_design_request