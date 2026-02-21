from django.contrib import admin

from .models import BudgetLimit, Category, Transaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ("name", "user")
    list_filter = ("user",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    autocomplete_fields = ["category"]
    list_display = ("date", "amount", "type", "category", "user")
    list_display_links = ("date",)
    list_editable = ("category",)
    list_filter = ("type", "category", "date")
    search_fields = ("description",)
    list_select_related = ("category", "user")
    date_hierarchy = "date"

    def save_model(self, request, obj, form, change):
        if not obj.user_id:
            obj.user = request.user
        super().save_model(request, obj, form, change)


@admin.register(BudgetLimit)
class BudgetLimitAdmin(admin.ModelAdmin):
    list_display = ("user", "category", "limit_amount", "period")
    list_filter = ("period",)
    list_select_related = ("user", "category")
