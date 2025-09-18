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