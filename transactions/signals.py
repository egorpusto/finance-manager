from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Category, Transaction


@receiver(post_save, sender=Transaction)
def check_transaction_against_limits(sender, instance, **kwargs):
    if instance.type == Transaction.EXPENSE:
        from .utils import check_budget_limits
        alerts = check_budget_limits(instance.user)
        if alerts:
            print(f"Budget limit exceeded: {alerts}")

    from django.core.cache import cache
    cache.delete(f'stats_{instance.user.id}')


@receiver(post_save, sender=User)
def create_default_categories(sender, instance, created, **kwargs):
    if created:
        default_categories = ['Food', 'Transport',
                              'Utilities', 'Entertainment']
        for cat_name in default_categories:
            if not Category.objects.filter(user=instance, name=cat_name).exists():
                Category.objects.create(name=cat_name, user=instance)
