from django.db.models import Sum
from datetime import timedelta
from django.utils import timezone


def check_budget_limits(user):
    from .models import BudgetLimit, Transaction
    alerts = []
    today = timezone.now().date()

    for budget in BudgetLimit.objects.filter(user=user):
        start_date = {
            'DAY': today,
            'WEEK': today - timedelta(days=today.weekday()),
            'MONTH': today.replace(day=1)
        }[budget.period]

        expenses = Transaction.objects.filter(
            user=user,
            category=budget.category,
            type=Transaction.EXPENSE,
            date__gte=start_date
        ).aggregate(total=Sum('amount'))['total'] or 0

        if expenses > budget.limit_amount:
            alerts.append({
                'category': budget.category.name,
                'spent': expenses,
                'limit': budget.limit_amount,
                'period': budget.get_period_display()
            })

    return alerts
