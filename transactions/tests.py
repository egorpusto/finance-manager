from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Transaction


class TransactionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name="Test Category",
            user=self.user
        )

    def test_create_transaction(self):
        transaction = Transaction.objects.create(
            user=self.user,
            amount=1000,
            category=self.category
        )
        self.assertEqual(str(transaction), f"{transaction.date} - 1000")
