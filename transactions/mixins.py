from django.views.generic.edit import FormMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import BudgetLimit


class BudgetLimitMixin(LoginRequiredMixin, FormMixin):
    model = BudgetLimit
    template_name = 'transactions/budget_limit_form.html'
    success_url = reverse_lazy('transactions:budget-list')

    def get_queryset(self):
        return BudgetLimit.objects.filter(user=self.request.user)


class UserSpecificMixin:
    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


class SuccessMessageMixin:
    success_message = ""

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.success_message)
        return response
