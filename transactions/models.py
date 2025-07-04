from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from .managers import BudgetLimitManager, TransactionManager
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Category Name")
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="User")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'name'], name='unique_user_category')
        ]
        verbose_name = "Transaction Category"
        verbose_name_plural = "Transaction Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('transactions:category_detail', kwargs={'pk': self.pk})
    

class Transaction(models.Model):
    INCOME = 'income'
    EXPENSE = 'expense'
    TYPE_CHOICES = [
        (INCOME, 'Income'),
        (EXPENSE, 'Expense'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="User",
        null=False
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Amount"
    )
    date = models.DateField(verbose_name="Transaction Date")
    type = models.CharField(
        max_length=7,
        choices=TYPE_CHOICES,
        default=EXPENSE,
        verbose_name="Type"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Category"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )

    objects = TransactionManager()

    class Meta:
        verbose_name = "Financial Transaction"
        verbose_name_plural = "Financial Transactions"
        ordering = ['-date', '-id']
        indexes = [
            models.Index(fields=['user', 'date']),
        ]

    def __str__(self):
        return f"{self.date}: {self.amount} ({self.get_type_display()})"

    def get_absolute_url(self):
        return reverse('transactions:transaction_detail', kwargs={'pk': self.pk})


class BudgetLimit(models.Model):
    PERIOD_CHOICES = [
        ('DAY', 'Daily'),
        ('WEEK', 'Weekly'),
        ('MONTH', 'Monthly')
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="User"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        verbose_name="Category"
    )
    limit_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Limit Amount"
    )
    period = models.CharField(
        max_length=10,
        choices=PERIOD_CHOICES,
        verbose_name="Period"
    )

    objects = BudgetLimitManager()

    class Meta:
        unique_together = ('user', 'category', 'period')
        verbose_name = "Budget Limit"
        verbose_name_plural = "Budget Limits"

    def __str__(self):
        return f"{self.user.username}: {self.category.name} - {self.limit_amount} ({self.get_period_display()})"


def get_user_budget_alerts(user):
    from .utils import check_budget_limits
    return check_budget_limits(user)

UserModel = get_user_model()

UserModel.add_to_class('get_budget_alerts', get_user_budget_alerts)
