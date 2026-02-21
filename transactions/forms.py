from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import BudgetLimit, Category, Transaction


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]


class TransactionForm(forms.ModelForm):
    new_category = forms.CharField(
        required=False,
        label="Or create new category",
        widget=forms.TextInput(
            attrs={"placeholder": "Enter new category name", "class": "form-control"}
        ),
        error_messages={
            "invalid": (
                "Please select either an existing category "
                "or create a new one, not both"
            )
        },
    )
    type = forms.ChoiceField(
        choices=Transaction.TYPE_CHOICES,
        initial=Transaction.EXPENSE,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = Transaction
        fields = ["type", "amount", "date", "category", "description"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["category"].queryset = Category.objects.filter(user=user)
            self.fields["category"].required = False

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get("category")
        new_category = cleaned_data.get("new_category")

        if not category and not new_category:
            raise forms.ValidationError(
                "You must select a category or create a new one", code="invalid"
            )

        if category and new_category:
            raise forms.ValidationError(
                "Please select either an existing category "
                "or create a new one, not both",
                code="invalid",
            )

        return cleaned_data


class BudgetLimitForm(forms.ModelForm):
    limit_amount = forms.DecimalField(
        min_value=0.01,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"step": "0.01"}),
        label="Limit Amount",
        help_text="Enter positive value",
    )

    class Meta:
        model = BudgetLimit
        fields = ["category", "limit_amount", "period"]
        widgets = {
            "category": forms.Select(attrs={"class": "form-select"}),
            "period": forms.Select(choices=BudgetLimit.PERIOD_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if self.user:
            categories = Category.objects.filter(user=self.user)
            seen = set()
            unique_categories = []

            for cat in categories.order_by("name"):
                if cat.name not in seen:
                    seen.add(cat.name)
                    unique_categories.append(cat.id)

            self.fields["category"].queryset = Category.objects.filter(
                id__in=unique_categories
            ).order_by("name")

    def clean(self):
        cleaned_data = super().clean()
        if hasattr(self, "user") and self.user:
            if "category" in cleaned_data and "period" in cleaned_data:
                exclude_pk = self.instance.pk if self.instance else None
                if (
                    BudgetLimit.objects.filter(
                        user=self.user,
                        category=cleaned_data["category"],
                        period=cleaned_data["period"],
                    )
                    .exclude(pk=exclude_pk)
                    .exists()
                ):
                    period_display = dict(self.Meta.model.PERIOD_CHOICES).get(
                        cleaned_data["period"], cleaned_data["period"]
                    )
                    raise forms.ValidationError(
                        f"You've already set {period_display.lower()} limit "
                        f"for category '{cleaned_data['category'].name}'. "
                        "Please edit the existing limit."
                    )
        return cleaned_data


class CSVImportForm(forms.Form):
    csv_file = forms.FileField(
        label="CSV File",
        help_text=(
            "Allowed format: Date, Amount, Type (income/expense), "
            "Category, Description"
        ),
    )

    def clean_csv_file(self):
        file = self.cleaned_data["csv_file"]
        if not file.name.endswith(".csv"):
            raise forms.ValidationError("Only .csv files are allowed.")
        if file.size > 5 * 1024 * 1024:  # 5MB
            raise forms.ValidationError("File size must not exceed 5MB.")
        return file
