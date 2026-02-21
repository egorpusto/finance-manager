from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import BudgetLimitForm, TransactionForm
from .models import BudgetLimit, Category, Transaction
from .utils import check_budget_limits

User = get_user_model()


class BaseTestCase(TestCase):
    """Базовый класс с общими данными для всех тестов."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", email="test@example.com"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", password="testpass123", email="other@example.com"
        )
        self.category, _ = Category.objects.get_or_create(name="Food", user=self.user)
        self.client = Client()
        self.client.login(username="testuser", password="testpass123")


# ─── Models ───────────────────────────────────────────────────────────────────


class CategoryModelTest(BaseTestCase):

    def test_str(self):
        self.assertEqual(str(self.category), "Food")

    def test_unique_constraint(self):
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            Category.objects.create(name="Food", user=self.user)

    def test_same_name_different_users(self):
        """Одинаковое название категории у разных пользователей — допустимо."""
        category, _ = Category.objects.get_or_create(name="Food", user=self.other_user)
        self.assertEqual(category.name, "Food")


class TransactionModelTest(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.transaction = Transaction.objects.create(
            user=self.user,
            amount=Decimal("100.00"),
            category=self.category,
            type=Transaction.EXPENSE,
            description="Test",
            date="2026-01-01",
        )

    def test_str(self):
        self.assertIn("100.00", str(self.transaction))
        self.assertIn("Expense", str(self.transaction))

    def test_get_absolute_url(self):
        url = self.transaction.get_absolute_url()
        self.assertIn(str(self.transaction.pk), url)

    def test_manager_expenses(self):
        expenses = Transaction.objects.expenses(self.user)
        self.assertIn(self.transaction, expenses)

    def test_manager_income(self):
        income = Transaction.objects.income(self.user)
        self.assertNotIn(self.transaction, income)


# ─── Utils ──────────────────────────────────────────────────────────────────


class BudgetUtilsTest(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.budget = BudgetLimit.objects.create(
            user=self.user,
            category=self.category,
            limit_amount=Decimal("100.00"),
            period="MONTH",
        )

    def test_no_alerts_when_no_transactions(self):
        alerts = check_budget_limits(self.user)
        self.assertEqual(alerts, [])

    def test_warning_alert_at_80_percent(self):
        Transaction.objects.create(
            user=self.user,
            amount=Decimal("85.00"),
            category=self.category,
            type=Transaction.EXPENSE,
            date=timezone.now().date(),
        )
        alerts = check_budget_limits(self.user)
        # Проверяем что alert есть и процент посчитан верно
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["percentage"], 85.0)
        self.assertTrue(alerts[0]["is_warning"])
        self.assertFalse(alerts[0]["is_exceeded"])

    def test_exceeded_alert(self):
        Transaction.objects.create(
            user=self.user,
            amount=Decimal("150.00"),
            category=self.category,
            type=Transaction.EXPENSE,
            date=timezone.now().date(),
        )
        alerts = check_budget_limits(self.user)
        self.assertEqual(len(alerts), 1)
        self.assertTrue(alerts[0]["is_exceeded"])

    def test_income_does_not_trigger_alert(self):
        Transaction.objects.create(
            user=self.user,
            amount=Decimal("999.00"),
            category=self.category,
            type=Transaction.INCOME,
            date=timezone.now().date(),
        )
        alerts = check_budget_limits(self.user)
        self.assertEqual(alerts, [])


# ─── Views ────────────────────────────────────────────────────────────────────


class TransactionListViewTest(BaseTestCase):

    def test_redirects_if_not_logged_in(self):
        self.client.logout()
        response = self.client.get(reverse("transactions:list"))
        self.assertRedirects(
            response,
            f"{reverse('transactions:login')}?next={reverse('transactions:list')}",
        )

    def test_returns_200_for_authenticated(self):
        response = self.client.get(reverse("transactions:list"))
        self.assertEqual(response.status_code, 200)

    def test_shows_only_own_transactions(self):
        own = Transaction.objects.create(
            user=self.user,
            amount=100,
            type=Transaction.EXPENSE,
            category=self.category,
            date="2026-01-01",
        )
        other = Transaction.objects.create(
            user=self.other_user,
            amount=200,
            type=Transaction.EXPENSE,
            category=Category.objects.get_or_create(name="Food", user=self.other_user)[
                0
            ],
            date="2026-01-01",
        )
        response = self.client.get(reverse("transactions:list"))
        transactions = response.context["transactions"]
        self.assertIn(own, transactions)
        self.assertNotIn(other, transactions)


class TransactionDetailViewTest(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.transaction = Transaction.objects.create(
            user=self.user,
            amount=100,
            type=Transaction.EXPENSE,
            category=self.category,
            date="2026-01-01",
        )
        self.other_transaction = Transaction.objects.create(
            user=self.other_user,
            amount=200,
            type=Transaction.EXPENSE,
            category=Category.objects.get_or_create(name="Food", user=self.other_user)[
                0
            ],
            date="2026-01-01",
        )

    def test_owner_can_view(self):
        response = self.client.get(
            reverse(
                "transactions:transaction_detail", kwargs={"pk": self.transaction.pk}
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_other_user_gets_404(self):
        """Чужую транзакцию открыть нельзя — должен быть 404."""
        response = self.client.get(
            reverse(
                "transactions:transaction_detail",
                kwargs={"pk": self.other_transaction.pk},
            )
        )
        self.assertEqual(response.status_code, 404)


class CreateTransactionViewTest(BaseTestCase):

    def test_create_with_existing_category(self):
        response = self.client.post(
            reverse("transactions:create"),
            {
                "type": Transaction.EXPENSE,
                "amount": "50.00",
                "date": "2026-01-01",
                "category": self.category.pk,
                "description": "Lunch",
            },
        )
        self.assertRedirects(response, reverse("transactions:list"))
        self.assertTrue(
            Transaction.objects.filter(user=self.user, amount=Decimal("50.00")).exists()
        )

    def test_create_with_new_category(self):
        response = self.client.post(
            reverse("transactions:create"),
            {
                "type": Transaction.INCOME,
                "amount": "1000.00",
                "date": "2026-01-01",
                "new_category": "Salary",
                "description": "",
            },
        )
        self.assertRedirects(response, reverse("transactions:list"))
        self.assertTrue(Category.objects.filter(name="Salary", user=self.user).exists())

    def test_cannot_select_both_category_and_new_category(self):
        response = self.client.post(
            reverse("transactions:create"),
            {
                "type": Transaction.EXPENSE,
                "amount": "50.00",
                "date": "2026-01-01",
                "category": self.category.pk,
                "new_category": "NewCat",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)


class ExportTransactionsViewTest(BaseTestCase):

    def test_export_returns_csv(self):
        Transaction.objects.create(
            user=self.user,
            amount=100,
            type=Transaction.EXPENSE,
            category=self.category,
            date="2026-01-01",
        )
        response = self.client.get(reverse("transactions:export"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        content = response.content.decode()
        self.assertIn("Date", content)
        self.assertIn("100", content)

    def test_export_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("transactions:export"))
        self.assertEqual(response.status_code, 401)


# ─── Forms ────────────────────────────────────────────────────────────────────


class TransactionFormTest(BaseTestCase):

    def test_valid_with_existing_category(self):
        form = TransactionForm(
            data={
                "type": Transaction.EXPENSE,
                "amount": "100.00",
                "date": "2026-01-01",
                "category": self.category.pk,
                "description": "",
            },
            user=self.user,
        )
        self.assertTrue(form.is_valid())

    def test_invalid_without_category(self):
        form = TransactionForm(
            data={
                "type": Transaction.EXPENSE,
                "amount": "100.00",
                "date": "2026-01-01",
            },
            user=self.user,
        )
        self.assertFalse(form.is_valid())

    def test_invalid_with_both_categories(self):
        form = TransactionForm(
            data={
                "type": Transaction.EXPENSE,
                "amount": "100.00",
                "date": "2026-01-01",
                "category": self.category.pk,
                "new_category": "NewCat",
            },
            user=self.user,
        )
        self.assertFalse(form.is_valid())


class BudgetLimitFormTest(BaseTestCase):

    def test_valid_form(self):
        form = BudgetLimitForm(
            data={
                "category": self.category.pk,
                "limit_amount": "500.00",
                "period": "MONTH",
            },
            user=self.user,
        )
        self.assertTrue(form.is_valid())

    def test_duplicate_budget_raises_error(self):
        BudgetLimit.objects.create(
            user=self.user, category=self.category, limit_amount=100, period="MONTH"
        )
        form = BudgetLimitForm(
            data={
                "category": self.category.pk,
                "limit_amount": "200.00",
                "period": "MONTH",
            },
            user=self.user,
        )
        self.assertFalse(form.is_valid())
