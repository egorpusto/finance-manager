import logging

from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Category, Transaction

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Transaction)
def on_transaction_save(sender, instance, created, **kwargs):
    if instance.type == Transaction.EXPENSE:
        from .utils import check_budget_limits

        alerts = check_budget_limits(instance.user)
        for alert in alerts:
            if alert["is_exceeded"]:
                logger.warning(
                    "Budget exceeded for user=%s category=%s: spent=%s limit=%s",
                    instance.user.username,
                    alert["category"],
                    alert["spent"],
                    alert["limit"],
                )
                if created and instance.user.email:
                    from .tasks import send_budget_alert_email_task

                    send_budget_alert_email_task.delay(
                        user_email=instance.user.email,
                        username=instance.user.username,
                        alert=alert,
                    )

    cache.delete(f"stats_{instance.user.id}")


@receiver(post_delete, sender=Transaction)
def on_transaction_delete(sender, instance, **kwargs):
    cache.delete(f"stats_{instance.user.id}")


@receiver(post_save, sender=User)
def create_default_categories(sender, instance, created, **kwargs):
    if created:
        default_categories = ["Food", "Transport", "Utilities", "Entertainment"]
        Category.objects.bulk_create(
            [Category(name=name, user=instance) for name in default_categories]
        )
