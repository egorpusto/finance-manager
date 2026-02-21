import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_budget_alert_email_task(self, user_email, username, alert):
    """
    Фоновая задача отправки email при превышении бюджета.
    При ошибке повторяет попытку до 3 раз с интервалом 60 секунд.
    """
    subject = f"Budget Alert: {alert['category']} limit exceeded"
    message = (
        f"Hi {username},\n\n"
        f"You have exceeded your {alert['period'].lower()} budget limit "
        f"for category \"{alert['category']}\".\n\n"
        f"  Spent:  {alert['spent']:.2f}\n"
        f"  Limit:  {alert['limit']:.2f}\n"
        f"  Usage:  {alert['percentage']}%\n\n"
        f"Consider reviewing your expenses.\n\n"
        f"— Finance Manager"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        logger.info("Budget alert email sent to %s", user_email)
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", user_email, exc)
        raise self.retry(exc=exc)
