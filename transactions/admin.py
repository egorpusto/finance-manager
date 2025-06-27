from django.contrib import admin
from .models import Category, Transaction

class CategoryAdmin(admin.ModelAdmin):
    search_fields = ['name']

admin.site.register(Category, CategoryAdmin)

class TransactionAdmin(admin.ModelAdmin):
    autocomplete_fields = ['category']
    list_display = ('amount', 'date', 'category', 'user')

    list_editable = ('date', 'category')

    list_filter = ('category', 'date')

    search_fields = ('description',)

    def save_model(self, request, obj, form, change):
        if not obj.user_id:
            obj.user = request.user
        super().save_model(request, obj, form, change)

    def render_change_form(self, request, context, *args, **kwargs):
        context['adminform'].form.fields['category'].widget.can_add_related = True
        return super().render_change_form(request, context, *args, **kwargs)


admin.site.register(Transaction, TransactionAdmin)
