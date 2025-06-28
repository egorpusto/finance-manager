from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Category Name")
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="User")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'name'], name='unique_user_category')
        ]
        unique_together = ('name', 'user')
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
        verbose_name="User"
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
