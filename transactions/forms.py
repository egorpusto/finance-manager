from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Transaction, Category

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]


class TransactionForm(forms.ModelForm):
    new_category = forms.CharField(
        required=False,
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
