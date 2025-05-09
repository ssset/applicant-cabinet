
# applicant/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from utils.ocr_utils import process_attestation_image
from applications.models import Application
from django.utils import timezone
from static.views import SystemStatsView
from django.http import HttpRequest
from django.contrib.auth.models import AnonymousUser
from users.models import CustomUser
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_attestation_image_task(image_path):
    """Задача для обработки изображения аттестата."""
    average_grade = process_attestation_image(image_path)
    return average_grade

@shared_task(bind=True, max_retries=3, retry_backoff=True)
def send_email_task(self, subject, message, from_email, recipient_list, html_message=None):
    """Задача для отправки email с поддержкой HTML."""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Email sent successfully to {recipient_list}")
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_list}: {str(e)}")
        self.retry(countdown=60)  # Повторная попытка через 60 секунд
