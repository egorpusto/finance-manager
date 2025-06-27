from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, TransactionForm
from .models import Transaction, Category  # Добавьте Category
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy


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

class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'transactions/transaction_list.html'
    context_object_name = 'transactions'

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).select_related('category')


class CreateTransactionView(CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'transactions/create_transaction.html'
    success_url = reverse_lazy('transactions:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Создаем новую категорию если нужно
        new_category = form.cleaned_data.get('new_category')
        if new_category:
            category = Category.objects.create(
                name=new_category,
                user=self.request.user
            )
            form.instance.category = category

        form.instance.user = self.request.user
        return super().form_valid(form)
