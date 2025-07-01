from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Transaction, Category


class TransactionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.category = Category.objects.create(
            name="Test Category",
            user=self.user
        )


    def test_create_transaction(self):
        transaction = Transaction.objects.create(
            user=self.user,
            amount=1000,
            category=self.category,
            type=Transaction.EXPENSE,
            description="Test transaction",
            date="2023-01-01"
        )
        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.amount, 1000)
        self.assertEqual(str(transaction), f"{transaction.date}: 1000 (Expense)")
