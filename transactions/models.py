from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
class Transaction(models.Model):
    INCOME = 'IN'
    EXPENSE = 'EX'
    TYPE_CHOICES = [
        (INCOME, 'Income'),
        (EXPENSE, 'Expense'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    type = models.CharField(max_length=2, choices=TYPE_CHOICES)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.date} - {self.amount} ({self.get_type_display()})"