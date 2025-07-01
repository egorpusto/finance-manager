from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import BudgetLimit, Transaction, Category


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]


class TransactionForm(forms.ModelForm):
    new_category = forms.CharField(
        label='Or create new category',
        widget=forms.TextInput(
            attrs={'placeholder': 'Enter new category name'})
    )

    type = forms.ChoiceField(
        choices=Transaction.TYPE_CHOICES,
        widget=forms.RadioSelect,
        initial=Transaction.EXPENSE,
        label='Transaction Type'
    )

    class Meta:
        model = Transaction
        fields = ['type', 'amount', 'date', 'category', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'})
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['category'].queryset = Category.objects.filter(
                user=user
            ).order_by('name').distinct()
            self.fields['category'].required = False


class BudgetLimitForm(forms.ModelForm):
    limit_amount = forms.DecimalField(
        min_value=0.01,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'step': '0.01'}),
        label="Limit Amount",
        help_text="Enter positive value"
    )
    class Meta:
        model = BudgetLimit
        fields = ['category', 'limit_amount', 'period']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'period': forms.Select(attrs={'class': 'form-select'})
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['category'].queryset = Category.objects.filter(
                user=self.user)


    def clean(self):
        cleaned_data = super().clean()
        if hasattr(self, 'user') and self.user:
            if 'category' in cleaned_data and 'period' in cleaned_data:
                exclude_pk = self.instance.pk if self.instance else None
                if BudgetLimit.objects.filter(
                    user=self.user,
                    category=cleaned_data['category'],
                    period=cleaned_data['period']
                ).exclude(pk=exclude_pk).exists():
                    period_display = dict(self.Meta.model.PERIOD_CHOICES).get(
                        cleaned_data['period'],
                        cleaned_data['period']
                    )
                    raise forms.ValidationError(
                        f"Вы уже установили {period_display.lower()} лимит "
                        f"для категории '{cleaned_data['category'].name}'. "
                        f"Пожалуйста, отредактируйте существующий лимит."
                    )
        return cleaned_data
