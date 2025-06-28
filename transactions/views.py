from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.views.decorators.csrf import csrf_protect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from django.core.cache import cache
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from .serializers import TransactionSerializer
import csv


from .models import Transaction, Category, BudgetLimit
from .forms import RegisterForm, TransactionForm, BudgetLimitForm
from .utils import check_budget_limits
from .mixins import BudgetLimitMixin, UserSpecificMixin


from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication


@method_decorator(csrf_protect, name='dispatch')
class BaseView(LoginRequiredMixin):
    pass


class BaseTransactionView(BaseView):
    model = Transaction
    success_url = reverse_lazy('transactions:list')


class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'transactions/transaction_list.html'
    context_object_name = 'transactions'

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)\
            .select_related('category')\
            .order_by('-date')


class CreateTransactionView(LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'transactions/create_transaction.html'
    success_url = reverse_lazy('transactions:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        new_category = form.cleaned_data.get('new_category')
        if new_category:
            category = Category.objects.create(
                name=new_category,
                user=self.request.user
            )
            form.instance.category = category
        return super().form_valid(form)


class TransactionDetailView(BaseTransactionView, DetailView):
    template_name = 'transactions/transaction_detail.html'


@method_decorator(csrf_protect, name='dispatch')
class BudgetLimitUpdateView(BudgetLimitMixin, UpdateView):
    form_class = BudgetLimitForm


@method_decorator(csrf_protect, name='dispatch')
class BudgetLimitDeleteView(LoginRequiredMixin, DeleteView):
    model = BudgetLimit
    template_name = 'transactions/budget_limit_confirm_delete.html'
    success_url = reverse_lazy('transactions:budget-list')

    def get_queryset(self):
        return BudgetLimit.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


@method_decorator(csrf_protect, name='dispatch')
class BudgetLimitCreateView(LoginRequiredMixin, CreateView):
    model = BudgetLimit
    form_class = BudgetLimitForm
    template_name = 'transactions/budget_limit_form.html'
    success_url = reverse_lazy('transactions:budget-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


@method_decorator(csrf_protect, name='dispatch')
class BudgetLimitListView(LoginRequiredMixin, ListView):
    model = BudgetLimit
    template_name = 'transactions/budget_limit_list.html'
    context_object_name = 'budgets'

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


@login_required
def budget_alerts(request):
    alerts = check_budget_limits(request.user)
    return render(request, 'transactions/budget_alerts.html', {'alerts': alerts})


def export_transactions(request):
    if not request.user.is_authenticated:
        return HttpResponse('Unauthorized', status=401)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Amount', 'Type', 'Category', 'Description'])

    transactions = Transaction.objects.filter(
        user=request.user).select_related('category')

    for t in transactions:
        writer.writerow([
            t.date.strftime('%Y-%m-%d'),
            t.amount,
            t.get_type_display(),
            t.category.name if t.category else '',
            t.description
        ])

    return response


class CategoryDetailView(LoginRequiredMixin, DetailView):
    model = Category
    template_name = 'transactions/category_detail.html'
    context_object_name = 'category'

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


class TransactionViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)


@login_required
def statistics_view(request):
    cache_key = f'stats_{request.user.id}'
    data = cache.get(cache_key)

    if not data:
        income_data = (
            Transaction.objects
            .filter(user=request.user, type=Transaction.INCOME)
            .annotate(month=TruncMonth('date'))
            .values('month')
            .annotate(total=Sum('amount'))
            .order_by('month')
        )

        expense_data = (
            Transaction.objects
            .filter(user=request.user, type=Transaction.EXPENSE)
            .annotate(month=TruncMonth('date'))
            .values('month')
            .annotate(total=Sum('amount'))
            .order_by('month')
        )

        months = list({item['month'].strftime("%Y-%m") for item in income_data} |
                      {item['month'].strftime("%Y-%m") for item in expense_data})
        months.sort()

        income_amounts = {item['month'].strftime(
            "%Y-%m"): float(item['total']) for item in income_data}
        expense_amounts = {item['month'].strftime(
            "%Y-%m"): float(item['total']) for item in expense_data}

        data = {
            'months': months,
            'income': [income_amounts.get(month, 0) for month in months],
            'expense': [expense_amounts.get(month, 0) for month in months]
        }
        cache.set(cache_key, data, 60*15)

    return render(request, 'statistics.html', data)

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('transactions:list')
    else:
        form = RegisterForm()
    return render(
        request, 
        "registration/register.html", 
        {'form': form}
    )

@login_required
def home(request):
    return render(request, "transactions/home.html")


