import csv
import io
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.db.models import Sum

from .models import BudgetLimit, Category, Transaction


def get_period_start(period):
    today = datetime.now().date()
    if period == "DAY":
        return today
    elif period == "WEEK":
        return today - timedelta(days=today.weekday())
    elif period == "MONTH":
        return today.replace(day=1)
    return today


def check_budget_limits(user):
    budgets = BudgetLimit.objects.filter(user=user)
    alerts = []

    for budget in budgets:
        spent = (
            Transaction.objects.filter(
                user=user,
                category=budget.category,
                type=Transaction.EXPENSE,
                date__gte=get_period_start(budget.period),
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )

        if spent > 0:
            limit = float(budget.limit_amount)
            spent_float = float(spent)
            percentage = round((spent_float / limit) * 100, 1) if limit > 0 else 0

            alerts.append(
                {
                    "category": budget.category.name,
                    "spent": spent_float,
                    "limit": limit,
                    "period": budget.get_period_display(),
                    "percentage": percentage,
                    "is_exceeded": spent_float >= limit,
                    "is_warning": percentage >= 80,
                }
            )

    return alerts


def import_transactions_from_csv(file, user):
    """
    Парсит CSV файл и создаёт транзакции для пользователя.
    Возвращает словарь с результатами: created, errors.
    Ожидаемые колонки: Date, Amount, Type, Category, Description
    """
    created = []
    errors = []

    try:
        decoded = file.read().decode("utf-8-sig")  # utf-8-sig убирает BOM если он есть
    except UnicodeDecodeError:
        return {"created": [], "errors": ["File encoding error. Please use UTF-8."]}

    reader = csv.DictReader(io.StringIO(decoded))

    expected_fields = {"Date", "Amount", "Type", "Category", "Description"}
    if not reader.fieldnames or not expected_fields.issubset(set(reader.fieldnames)):
        missing = expected_fields - set(reader.fieldnames or [])
        return {
            "created": [],
            "errors": [f"Missing required columns: {', '.join(missing)}"],
        }

    for line_num, row in enumerate(
        reader, start=2
    ):  # start=2 т.к. строка 1 — заголовок
        row_errors = []

        try:
            date = datetime.strptime(row["Date"].strip(), "%Y-%m-%d").date()
        except ValueError:
            row_errors.append(
                f"Row {line_num}: invalid date '{row['Date']}' (expected YYYY-MM-DD)"
            )

        try:
            amount = Decimal(row["Amount"].strip())
            if amount <= 0:
                row_errors.append(f"Row {line_num}: amount must be greater than zero")
        except InvalidOperation:
            row_errors.append(f"Row {line_num}: invalid amount '{row['Amount']}'")

        transaction_type = row["Type"].strip().lower()
        if transaction_type not in [Transaction.INCOME, Transaction.EXPENSE]:
            row_errors.append(
                f"Row {line_num}: invalid type '{row['Type']}' "
                f"(expected 'income' or 'expense')"
            )

        if row_errors:
            errors.extend(row_errors)
            continue

        category_name = row["Category"].strip()
        category = None
        if category_name:
            category, _ = Category.objects.get_or_create(name=category_name, user=user)

        transaction = Transaction.objects.create(
            user=user,
            date=date,
            amount=amount,
            type=transaction_type,
            category=category,
            description=row["Description"].strip(),
        )
        created.append(transaction)

    return {"created": created, "errors": errors}
