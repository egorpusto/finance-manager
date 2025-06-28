from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Category


@receiver(post_save, sender=User)
def create_default_categories(sender, instance, created, **kwargs):
    if created:
        default_categories = ['Food', 'Transport',
                              'Utilities', 'Entertainment']
        for cat_name in default_categories:
            if not Category.objects.filter(user=instance, name=cat_name).exists():
                Category.objects.create(name=cat_name, user=instance)
