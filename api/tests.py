# from django.test import TestCase
# from django.contrib.auth import get_user_model

# User = get_user_model()

# from rest_framework.test import APIClient
# from rest_framework import status


# class ShoppingCartViewSetTest(TestCase):
#     def setUp(self):
#         self.client = APIClient()
#         self.url = '/shoppingcarts/'

#     def create_users_and_carts(self):
#         self.user1 = User.objects.create_user(username='Jecinta', password='jeci4567JM')
#         self.user2 = User.objects.create_user(username='Daniella', password='dan6783D@')
#         from cart.models import ShoppingCart  # Import after User load
#         self.cart1 = ShoppingCart.objects.create(user=self.user1)
#         self.cart2 = ShoppingCart.objects.create(user=self.user2)
#         # Debug info
#         print(f"user1 type: {type(self.user1)}")
#         print(f"ShoppingCart.user related_model: {ShoppingCart._meta.get_field('user').related_model}")

#     def test_list_shopping_carts_authenticated(self):
#         self.create_users_and_carts()
#         self.client.force_authenticate(user=self.user1)
#         response = self.client.get(self.url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.data), 1)
#         self.assertEqual(response.data[0]['user'], self.user1.id)

#     def test_create_shopping_cart_authenticated(self):
#         self.create_users_and_carts()
#         self.client.force_authenticate(user=self.user2)
#         response = self.client.post(self.url, {})
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertEqual(response.data['user'], self.user2.id)

#     def test_create_shopping_cart_unauthenticated(self):
#         self.create_users_and_carts()
#         self.client.force_authenticate(user=None)
#         response = self.client.post(self.url, {})
#         self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# class CartItemViewSetTest(TestCase):
#     def setUp(self):
#         self.client = APIClient()
#         self.url = '/cartitems/'

#     def create_data(self):
#         self.user1 = User.objects.create_user(username='Jecinta', password='jeci4567JM')
#         self.user2 = User.objects.create_user(username='Daniella', password='dan6783D@')
#         from cart.models import ShoppingCart, CartItem
#         from products.models import Inventory
#         self.cart1 = ShoppingCart.objects.create(user=self.user1)
#         self.cart2 = ShoppingCart.objects.create(user=self.user2)
#         self.inventory1 = Inventory.objects.create(description='Item 1', price=10.0, artisan_id=self.user1)
#         # Debug info
#         print(f"user1 type: {type(self.user1)}")
#         print(f"ShoppingCart.user related_model: {ShoppingCart._meta.get_field('user').related_model}")

#     def test_list_cart_items_authenticated(self):
#         self.create_data()
#         from cart.models import CartItem
#         CartItem.objects.create(cart=self.cart1, inventory=self.inventory1, quantity=1, price_when_added=10.0)
#         self.client.force_authenticate(user=self.user1)
#         response = self.client.get(self.url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.data), 1)

#     def test_create_cart_item_owner(self):
#         self.create_data()
#         self.client.force_authenticate(user=self.user1)
#         data = {'cart': self.cart1.id, 'inventory': self.inventory1.id, 'quantity': 2}
#         response = self.client.post(self.url, data)
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertEqual(response.data['price_when_added'], 10.0)

#     def test_create_cart_item_not_owner_forbidden(self):
#         self.create_data()
#         self.client.force_authenticate(user=self.user1)
#         data = {'cart': self.cart2.id, 'inventory': self.inventory1.id, 'quantity': 2}
#         response = self.client.post(self.url, data)
#         self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# class InventoryViewSetTest(TestCase):
#     def setUp(self):
#         self.client = APIClient()
#         self.url = '/inventories/'

#     def create_users(self):
#         self.artisan_user = User.objects.create_user(username='artisan', password='pass')
#         self.artisan_user.user_type = 'artisan'
#         self.artisan_user.save()
#         self.other_user = User.objects.create_user(username='other', password='pass')

#     def test_create_inventory_authenticated_artisan(self):
#         self.create_users()
#         self.client.force_authenticate(user=self.artisan_user)
#         data = {'description': 'New Item', 'price': 20.0}
#         response = self.client.post(self.url, data)
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertEqual(response.data['artisan_id'], self.artisan_user.id)

#     def test_create_inventory_unauthenticated(self):
#         self.create_users()
#         self.client.force_authenticate(user=None)
#         data = {'description': 'New Item', 'price': 20.0}
#         response = self.client.post(self.url, data)
#         self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

#     def test_create_inventory_not_artisan(self):
#         self.create_users()
#         self.client.force_authenticate(user=self.other_user)
#         data = {'description': 'New Item', 'price': 20.0}
#         response = self.client.post(self.url, data)
#         self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
