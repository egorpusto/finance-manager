import csv

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .forms import BudgetLimitForm, CSVImportForm, RegisterForm, TransactionForm
from .models import BudgetLimit, Category, Transaction
from .serializers import (
    BudgetLimitSerializer,
    CategorySerializer,
    TransactionSerializer,
)
from .utils import check_budget_limits, import_transactions_from_csv


@method_decorator(csrf_protect, name="dispatch")
class BaseView(LoginRequiredMixin):
    pass


class BaseTransactionView(BaseView):
    model = Transaction
    success_url = reverse_lazy("transactions:list")


class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    model = Transaction
    template_name = "transactions/transaction_confirm_delete.html"
    success_url = reverse_lazy("transactions:list")

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    def get_success_url(self):
        messages.success(self.request, "Transaction deleted successfully")
        return super().get_success_url()


class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = "transactions/transaction_list.html"
    context_object_name = "transactions"
    paginate_by = 10

    def get_queryset(self):
        queryset = (
            Transaction.objects.filter(user=self.request.user)
            .select_related("category")
            .order_by("-date")
        )

        transaction_type = self.request.GET.get("type")
        if transaction_type in [Transaction.INCOME, Transaction.EXPENSE]:
            queryset = queryset.filter(type=transaction_type)

        category_id = self.request.GET.get("category")
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["alerts"] = check_budget_limits(self.request.user)
        context["categories"] = Category.objects.filter(
            user=self.request.user
        ).order_by("name")

        return context


class CreateTransactionView(LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "transactions/create_transaction.html"
    success_url = reverse_lazy("transactions:list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        new_category = form.cleaned_data.get("new_category")

        if new_category:
            category, created = Category.objects.get_or_create(
                name=new_category, user=self.request.user
            )
            form.instance.category = category

        return super().form_valid(form)


class TransactionDetailView(BaseTransactionView, DetailView):
    template_name = "transactions/transaction_detail.html"

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)


@method_decorator(csrf_protect, name="dispatch")
class BudgetLimitUpdateView(LoginRequiredMixin, UpdateView):
    model = BudgetLimit
    form_class = BudgetLimitForm
    template_name = "transactions/budget_limit_form.html"
    success_url = reverse_lazy("transactions:budget-list")

    def get_queryset(self):
        return BudgetLimit.objects.filter(user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


@method_decorator(csrf_protect, name="dispatch")
class BudgetLimitDeleteView(LoginRequiredMixin, DeleteView):
    model = BudgetLimit
    template_name = "transactions/budget_limit_confirm_delete.html"
    success_url = reverse_lazy("transactions:budget-list")

    def get_queryset(self):
        return BudgetLimit.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


@method_decorator(csrf_protect, name="dispatch")
class BudgetLimitCreateView(LoginRequiredMixin, CreateView):
    model = BudgetLimit
    form_class = BudgetLimitForm
    template_name = "transactions/budget_limit_form.html"
    success_url = reverse_lazy("transactions:budget-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


@method_decorator(csrf_protect, name="dispatch")
class BudgetLimitListView(LoginRequiredMixin, ListView):
    model = BudgetLimit
    template_name = "transactions/budget_limit_list.html"
    context_object_name = "budgets"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["alerts"] = check_budget_limits(self.request.user)
        return context

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


def export_transactions(request):
    if not request.user.is_authenticated:
        return HttpResponse("Unauthorized", status=401)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="transactions.csv"'

    writer = csv.writer(response)
    writer.writerow(["Date", "Amount", "Type", "Category", "Description"])

    transactions = Transaction.objects.filter(user=request.user).select_related(
        "category"
    )

    for t in transactions:
        writer.writerow(
            [
                t.date.strftime("%Y-%m-%d"),
                t.amount,
                t.get_type_display(),
                t.category.name if t.category else "",
                t.description,
            ]
        )

    return response


class CategoryDetailView(LoginRequiredMixin, DetailView):
    model = Category
    template_name = "transactions/category_detail.html"
    context_object_name = "category"

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["type", "category"]
    ordering_fields = ["date", "amount"]
    ordering = ["-date"]

    def get_queryset(self):
        queryset = Transaction.objects.filter(user=self.request.user).select_related(
            "category"
        )

        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        """Сводка: общий доход, расход и баланс пользователя."""
        from django.db.models import Sum

        qs = Transaction.objects.filter(user=request.user)
        income = (
            qs.filter(type=Transaction.INCOME).aggregate(total=Sum("amount"))["total"]
            or 0
        )
        expense = (
            qs.filter(type=Transaction.EXPENSE).aggregate(total=Sum("amount"))["total"]
            or 0
        )
        return Response(
            {
                "income": float(income),
                "expense": float(expense),
                "balance": float(income - expense),
            }
        )


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BudgetLimitViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetLimitSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BudgetLimit.objects.filter(user=self.request.user).select_related(
            "category"
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@login_required
def statistics_view(request):
    cache_key = f"stats_{request.user.id}"
    data = cache.get(cache_key)

    if not data:
        income_data = (
            Transaction.objects.filter(user=request.user, type=Transaction.INCOME)
            .annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(total=Sum("amount"))
            .order_by("month")
        )

        expense_data = (
            Transaction.objects.filter(user=request.user, type=Transaction.EXPENSE)
            .annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(total=Sum("amount"))
            .order_by("month")
        )

        months = list(
            {item["month"].strftime("%Y-%m") for item in income_data}
            | {item["month"].strftime("%Y-%m") for item in expense_data}
        )
        months.sort()

        income_amounts = {
            item["month"].strftime("%Y-%m"): float(item["total"])
            for item in income_data
        }
        expense_amounts = {
            item["month"].strftime("%Y-%m"): float(item["total"])
            for item in expense_data
        }

        data = {
            "months": months,
            "income": [income_amounts.get(month, 0) for month in months],
            "expense": [expense_amounts.get(month, 0) for month in months],
        }
        cache.set(cache_key, data, 60 * 15)

    return render(request, "statistics.html", data)


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("transactions:list")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})


@login_required
def home(request):
    recent_transactions = (
        Transaction.objects.filter(user=request.user)
        .select_related("category")
        .order_by("-date")[:5]
    )

    context = {
        "alerts": check_budget_limits(request.user),
        "recent_transactions": recent_transactions,
    }
    return render(request, "transactions/home.html", context)


@login_required
def import_transactions(request):
    if request.method == "POST":
        form = CSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            result = import_transactions_from_csv(
                request.FILES["csv_file"], request.user
            )
            created_count = len(result["created"])
            errors = result["errors"]

            if created_count:
                messages.success(
                    request, f"Successfully imported {created_count} transaction(s)."
                )
            if errors:
                for error in errors:
                    messages.warning(request, error)
            if not created_count and not errors:
                messages.info(request, "The file was empty or had no valid rows.")

            return redirect("transactions:list")
    else:
        form = CSVImportForm()

    return render(request, "transactions/import_transactions.html", {"form": form})
