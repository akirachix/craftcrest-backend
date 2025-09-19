import uuid
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from users.models import User, ArtisanProfile, Profile, ArtisanPortfolio, PortfolioImage
from api.serializers import UserRegistrationSerializer
from datetime import timedelta
from unittest.mock import patch
import os
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
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

def create_test_image():
    file = BytesIO()
    image = Image.new('RGB', (100, 100), color='red')
    image.save(file, 'JPEG')
    file.seek(0)
    return SimpleUploadedFile(f"test_image.jpg", file.getvalue(), content_type="image/jpeg")

class UserModelTest(TestCase):
    def setUp(self):
        self.user_data = {
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Kinyanjui",
            "phone_number": "1234567890",
            "user_type": User.BUYER,
        }
        self.user = User.objects.create(**self.user_data)
        self.user.set_password("TestPassword123")
        self.user.save()

    def test_user_str(self):
        self.assertEqual(str(self.user), "John Kinyanjui (test@example.com)")

    def test_generate_otp(self):
        self.user.generate_otp()
        self.assertTrue(len(self.user.otp) == 6)
        self.assertFalse(self.user.otp_verified)
        self.assertTrue(self.user.otp_exp > timezone.now())

    def test_verify_otp_success(self):
        self.user.generate_otp()
        otp = self.user.otp
        result = self.user.verify_otp(otp)
        self.assertTrue(result)
        self.assertTrue(self.user.otp_verified)

    def test_verify_otp_expired(self):
        self.user.generate_otp()
        self.user.otp_exp = timezone.now() - timedelta(minutes=1)
        self.user.save()
        result = self.user.verify_otp(self.user.otp)
        self.assertFalse(result)
        self.assertFalse(self.user.otp_verified)

    def test_verify_otp_invalid(self):
        self.user.generate_otp()
        result = self.user.verify_otp("999999")
        self.assertFalse(result)
        self.assertFalse(self.user.otp_verified)


class ArtisanProfileModelTest(TestCase):
    def setUp(self):
        self.artisan = User.objects.create(
            email="artisan@example.com",
            first_name="John",
            last_name="Kinyanjui",
            phone_number="0987654321",
            user_type=User.ARTISAN
        )
        self.artisan.set_password("TestPassword123")
        self.artisan.save()
        self.artisan_profile = ArtisanProfile.objects.create(user=self.artisan)

    def test_artisan_profile_str(self):
        self.assertEqual(str(self.artisan_profile), "Artisan Profile for artisan@example.com")

    def test_clean_invalid_user_type(self):
        buyer = User.objects.create(
            email="buyer@example.com",
            first_name="Mary",
            last_name="Wanjiku",
            phone_number="1234567890",
            user_type=User.BUYER
        )
        buyer.set_password("TestPassword123")
        buyer.save()
        invalid_profile = ArtisanProfile(user=buyer)
        with self.assertRaisesMessage(Exception, "ArtisanProfile can only be linked to an artisan user."):
            invalid_profile.clean()

    def test_update_verification_status_verified(self):
        self.artisan_profile.fulfillment_rate = 95.0
        self.artisan_profile.rejection_rate = 5.0
        self.artisan_profile.average_rating = 4.5
        self.artisan_profile.days_active = 100
        self.artisan_profile.completed_orders = 15
        self.artisan_profile.update_verification_status()
        self.assertTrue(self.artisan_profile.is_verified)
        self.assertIsNone(self.artisan_profile.order_value_limit)

    def test_can_take_order_verified(self):
        self.artisan_profile.is_verified = True
        self.assertTrue(self.artisan_profile.can_take_order(3000))

    def test_can_take_order_unverified_limit(self):
        self.artisan_profile.is_verified = False
        self.artisan_profile.weekly_order_count = 3
        self.assertTrue(self.artisan_profile.can_take_order(1500))
        self.assertFalse(self.artisan_profile.can_take_order(2500))

    def test_can_take_order_unverified_weekly_limit(self):
        self.artisan_profile.is_verified = False
        self.artisan_profile.weekly_order_count = 5
        self.assertFalse(self.artisan_profile.can_take_order(1500))


class UserRegistrationSerializerTest(TestCase):
    def setUp(self):
        self.valid_data = {
            "email": "newuser@example.com",
            "password": "TestPassword123",
            "first_name": "John",
            "last_name": "Kinyanjui",
            "phone_number": "1234567890",
            "user_type": "buyer"
        }

    def test_valid_buyer_data(self):
        serializer = UserRegistrationSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())

    def test_valid_artisan_data(self):
        artisan_data = {
            **self.valid_data,
            "user_type": "artisan",
            "national_id": "1234567890",
            "latitude": 1.234567,
            "longitude": 2.345678,
            "portfolio": {
                "title": "Test Portfolio",
                "description": "A test portfolio",
                "image_files": [create_test_image() for _ in range(10)]  
            }
        }
        with patch('api.serializers.ArtisanPortfolioSerializer.is_valid', return_value=True):
            with patch('api.serializers.ArtisanPortfolioSerializer.validated_data', return_value={
                "title": "Test Portfolio",
                "description": "A test portfolio",
                "image_files": artisan_data["portfolio"]["image_files"]
            }):
                serializer = UserRegistrationSerializer(data=artisan_data)
                self.assertTrue(serializer.is_valid(), f"Serializer errors: {serializer.errors}")

    def test_missing_required_fields(self):
        invalid_data = {
            "email": "newuser@example.com",
            "password": "TestPassword123",
        }
        serializer = UserRegistrationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        expected_errors = ["first_name", "last_name", "phone_number", "user_type"]
        self.assertTrue(any(field in serializer.errors for field in expected_errors),
                        f"Expected one of {expected_errors}, got {serializer.errors}")

    def test_invalid_email(self):
        invalid_data = {**self.valid_data, "email": "invalid-email"}
        serializer = UserRegistrationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_register_artisan_missing_portfolio(self):
        artisan_data = {
            **self.valid_data,
            "user_type": "artisan",
            "national_id": "1234567890",
            "latitude": 1.234567,
            "longitude": 2.345678,
        }
        serializer = UserRegistrationSerializer(data=artisan_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("portfolio", serializer.errors)


class UserRegistrationViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("register") 
        self.valid_buyer_data = {
            "email": "buyer@example.com",
            "password": "TestPassword123",
            "first_name": "John",
            "last_name": "Kinyanjui",
            "phone_number": "1234567890",
            "user_type": "buyer"
        }

    def test_register_buyer_success(self):
        with patch('users.utils.send_otp_email'):  
            response = self.client.post(self.url, self.valid_buyer_data, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn("id", response.data)
            self.assertIn("token", response.data)
            user = User.objects.get(email=self.valid_buyer_data["email"])
            self.assertFalse(user.is_active)

    def test_register_duplicate_email(self):
        User.objects.create(
            email="buyer@example.com",
            phone_number="0987654321",
            user_type=User.BUYER,
            first_name="Mary",
            last_name="Wanjiku"
        )
        with patch('users.utils.send_otp_email'):
            response = self.client.post(self.url, self.valid_buyer_data, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("email", response.data)


class LoginViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("login")
        self.user = User.objects.create(
            email="test@example.com",
            phone_number="1234567890",
            user_type=User.BUYER,
            is_active=True,
            first_name="John",
            last_name="Kinyanjui"
        )
        self.user.set_password("TestPassword123")
        self.user.save()

    def test_login_with_email_success(self):
        data = {"email": "test@example.com", "password": "TestPassword123"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertIn("user", response.data)

    def test_login_with_phone_success(self):
        data = {"phone_number": "1234567890", "password": "TestPassword123"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)

    def test_login_invalid_credentials(self):
        data = {"email": "test@example.com", "password": "WrongPassword"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)


class OTPVerificationViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("verify-otp")  
        self.user = User.objects.create(
            email="test@example.com",
            phone_number="1234567890",
            user_type=User.BUYER,
            is_active=False,
            first_name="John",
            last_name="Kinyanjui"
        )
        self.user.generate_otp()
        self.user.set_password("TestPassword123")
        self.user.save()

    def test_verify_otp_success(self):
        data = {"email": "test@example.com", "otp": self.user.otp}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.otp_verified)
        self.assertTrue(self.user.is_active)

    def test_verify_otp_invalid(self):
        data = {"email": "test@example.com", "otp": "999999"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("otp", response.data)

    def test_verify_otp_expired(self):
        self.user.otp_exp = timezone.now() - timedelta(minutes=1)
        self.user.save()
        data = {"email": "test@example.com", "otp": self.user.otp}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("otp", response.data)



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

