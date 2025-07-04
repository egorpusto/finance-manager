from django.db.models import Sum
from .models import BudgetLimit, Transaction
from datetime import datetime, timedelta


def get_period_start(period):
    today = datetime.now().date()
    if period == 'DAY':
        return today
    elif period == 'WEEK':
        return today - timedelta(days=today.weekday())
    elif period == 'MONTH':
        return today.replace(day=1)
    return today


def check_budget_limits(user):
    budgets = BudgetLimit.objects.filter(user=user)
    alerts = []

    for budget in budgets:
        spent = Transaction.objects.filter(
            user=user,
            category=budget.category,
            type=Transaction.EXPENSE,
            date__gte=get_period_start(budget.period)
        ).aggregate(total=Sum('amount'))['total'] or 0

        if spent > 0:
            alerts.append({
                'category': budget.category.name,
                'spent': float(spent),
                'limit': float(budget.limit_amount),
                'period': budget.get_period_display()
            })

    return alerts
