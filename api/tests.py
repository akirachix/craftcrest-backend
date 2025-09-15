from unittest.mock import patch
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from users.models import ArtisanPortfolio

User = get_user_model()


class AuthTests(APITestCase):
    def setUp(self):
        self.register_url = "/api/register/"
        self.login_url = "/api/login/"
        self.portfolio_url = "/api/portfolio/"

    @patch("api.serializers.send_forgot_password_email")  
    def test_register_user_success(self, mock_send_email):
        data = {
            "first_name": "John",
            "last_name": "Kinyanjui",
            "email": "john@example.com",
            "phone_number": "0712345678",
            "password": "password123",
            "user_type": "ARTISAN",
            "national_id": "12345678",
            "latitude": 1.2921,
            "longitude": 36.8219,
            "portfolio": {
                "title": "My Portfolio",
                "description": "Some description about portfolio",
                "image_urls": [f"http://example.com/img{i}.jpg" for i in range(10)],
            },
        }
        response = self.client.post(self.register_url, data, format="json")
        print("Register response data:", response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="john@example.com").exists())
        mock_send_email.assert_called_once()

    def test_register_missing_required_fields(self):
        data = {
            "first_name": "Jane",
            "password": "pass123",
            "user_type": "BUYER",
            "phone_number": "0712345678",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_register_invalid_email_format(self):
        data = {
            "email": "not-an-email",
            "password": "pass123",
            "first_name": "Jane",
            "last_name": "Doe",
            "user_type": "BUYER",
            "phone_number": "0712345678",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_register_invalid_phone_number_letters(self):
        data = {
            "email": "jane@example.com",
            "password": "pass123",
            "first_name": "Jane",
            "last_name": "Doe",
            "user_type": "BUYER",
            "phone_number": "07ab345678",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone_number", response.data)

    def test_register_artisan_missing_portfolio(self):
        data = {
            "email": "jane@example.com",
            "password": "saltedpass",
            "first_name": "Jane",
            "last_name": "Doe",
            "user_type": "ARTISAN",
            "phone_number": "0712345679",
            "national_id": "987654321",
            "latitude": 1.1,
            "longitude": 36.8,
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("portfolio", response.data)


class PortfolioTests(APITestCase):
    def setUp(self):
        self.portfolio_url = "/api/portfolio/"
        self.artisan = User.objects.create_user(
            email="artisan@example.com",
            phone_number="0733333333",
            password="artisanpass",
            user_type="ARTISAN",
        )
        self.buyer = User.objects.create_user(
            email="buyer@example.com",
            phone_number="0744444444",
            password="buyerpass",
            user_type="BUYER",
        )
        self.admin = User.objects.create_superuser(email="admin@example.com", password="adminpass")
        self.admin.user_type = "ADMIN"
        self.admin.save()
        Token.objects.create(user=self.admin)

    def authenticate(self, user, password):
        response = self.client.post(
            "/api/login/", {"identifier": user.email, "password": password}, format="json"
        )
        token = response.data.get("token")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

    def test_artisan_can_create_portfolio(self):
        self.authenticate(self.artisan, "artisanpass")
        data = {
            "title": "Test Portfolio",
            "description": "A test description",
            "image_urls": [f"http://example.com/img{i}.jpg" for i in range(10)],
        }
        response = self.client.post(self.portfolio_url, data, format="json")
        print("Create portfolio response data:", response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_portfolio_create_with_invalid_image_urls(self):
        self.authenticate(self.artisan, "artisanpass")
        data = {
            "title": "Some Portfolio",
            "description": "Testing invalid image URLs",
            "image_urls": [
                "http://valid-url.com/img.jpg",
                "invalid-url",
            ],
        }
        response = self.client.post(self.portfolio_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("image_urls", response.data)

    def test_artisan_cannot_create_portfolio_with_less_than_10_images(self):
        self.authenticate(self.artisan, "artisanpass")
        data = {
            "title": "Incomplete Portfolio",
            "description": "Not enough images",
            "image_urls": ["http://example.com/img1.jpg"],
        }
        response = self.client.post(self.portfolio_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_buyer_cannot_create_portfolio(self):
        self.authenticate(self.buyer, "buyerpass")
        data = {
            "title": "Buyer Portfolio",
            "description": "Buyers cannot create portfolios",
            "image_urls": [f"http://example.com/img{i}.jpg" for i in range(10)],
        }
        response = self.client.post(self.portfolio_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_view_all_portfolios(self):
        self.authenticate(self.admin, "adminpass")
        ArtisanPortfolio.objects.create(
            artisan=self.artisan,
            title="Admin View Portfolio",
            description="Portfolio created for admin view test",
            image_urls=[f"http://example.com/img{i}.jpg" for i in range(10)],
        )
        response = self.client.get(self.portfolio_url, format="json")
        print("Admin view portfolios response data:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_buyer_can_view_portfolios_but_not_edit(self):
        self.authenticate(self.buyer, "buyerpass")
        response = self.client.get(self.portfolio_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data_edit = {
            "title": "Trying to edit",
            "description": "Change description",
            "image_urls": [f"http://example.com/img{i}.jpg" for i in range(10)],
        }
        response_post = self.client.post(self.portfolio_url, data_edit, format="json")
        self.assertEqual(response_post.status_code, status.HTTP_403_FORBIDDEN)
