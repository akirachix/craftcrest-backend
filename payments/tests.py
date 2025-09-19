from django.test import TestCase
from django.utils import timezone
from users.models import User
from orders.models import Order
from payments.models import Payment

# Create your tests here.
class PaymentModelTest(TestCase):
    def setUp(self):
        self.buyer = User.objects.create(
            user_type='buyer',
            first_name='Buyer',
            last_name='Test',
            email='buyer@test.com',
            phone_number='0712345678',
            national_id='12345678'
        )
        self.artisan = User.objects.create(
            user_type='artisan',
            first_name='Artisan',
            last_name='Test',
            email='artisan@test.com',
            phone_number='0798765432',
            national_id='87654321'
        )
        self.order = Order.objects.create(
            buyer_id=self.buyer,
            artisan_id=self.artisan,
            quantity=1,
            total_amount=500.00,
            order_type='custom',
            status='pending'
        )

    # def test_create_held_payment(self):
    #     payment = Payment.objects.create(
    #         order_id=self.order,
    #         artisan_id=self.artisan,
    #         amount=500.00,
    #         transaction_code='TX12345',
    #         status='held',
    #         buyer_phone=self.buyer.phone_number,
    #         artisan_phone=self.artisan.phone_number,
    #         paid_at=timezone.now()
    #     )
    #     self.assertEqual(payment.status, 'held')
    #     self.assertTrue(payment.held_by_platform)
    #     self.assertEqual(payment.amount, 500.00)
    #     self.assertEqual(payment.buyer_phone, '0712345678')
    #     self.assertEqual(payment.artisan_phone, '0798765432')

    # def test_release_payment(self):
    #     payment = Payment.objects.create(
    #         order_id=self.order,
    #         artisan_id=self.artisan,
    #         amount=500.00,
    #         transaction_code='TX12345',
    #         status='held',
    #         buyer_phone=self.buyer.phone_number,
    #         artisan_phone=self.artisan.phone_number,
    #         paid_at=timezone.now()
    #     )
    #     payment.status = 'released'
    #     payment.released_at = timezone.now()
    #     payment.held_by_platform = False
    #     payment.save()
    #     self.assertEqual(payment.status, 'released')
    #     self.assertFalse(payment.held_by_platform)
    #     self.assertIsNotNone(payment.released_at)

    # def test_refund_payment(self):
    #     payment = Payment.objects.create(
    #         order_id=self.order,
    #         artisan_id=self.artisan,
    #         amount=500.00,
    #         transaction_code='TX12345',
    #         status='held',
    #         buyer_phone=self.buyer.phone_number,
    #         artisan_phone=self.artisan.phone_number,
    #         paid_at=timezone.now()
    #     )
    #     payment.status = 'refunded'
    #     payment.refunded_reason = 'Buyer rejected product'
    #     payment.held_by_platform = False
    #     payment.save()
    #     self.assertEqual(payment.status, 'refunded')
    #     self.assertEqual(payment.refunded_reason, 'Buyer rejected product')
    #     self.assertFalse(payment.held_by_platform)