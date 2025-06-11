from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from utils.ocr_utils import process_attestation_image
from applications.models import Application
from django.utils import timezone
from static.views import SystemStatsView
from django.http import HttpRequest
from django.contrib.auth.models import AnonymousUser
from users.models import CustomUser, ApplicantProfile  # Добавляем импорт ApplicantProfile
import logging

logger = logging.getLogger('applicant')


@shared_task
def process_attestation_image_task(profile_id, image_path):
    """
    Celery task to process attestation image, calculate average grade, and update ApplicantProfile.
    """
    logger.debug(f"Task started: process_attestation_image_task, profile_id={profile_id}, image_path={image_path}")

    try:
        logger.info(f"Processing image for profile {profile_id}: {image_path}")
        average_grade = process_attestation_image(image_path)

        # Обновляем профиль
        profile = ApplicantProfile.objects.get(id=profile_id)
        profile.calculated_average_grade = average_grade
        profile.task_id = None  # Сбрасываем task_id
        profile.save()

        logger.info(
            f"Task completed: process_attestation_image_task, profile_id={profile_id}, average_grade={average_grade}")
        return average_grade
    except ApplicantProfile.DoesNotExist:
        logger.error(f"Profile {profile_id} not found")
        raise Exception(f"Profile {profile_id} not found")
    except Exception as e:
        logger.error(f"Task failed: process_attestation_image_task, profile_id={profile_id}, error={str(e)}",
                     exc_info=True)
        raise


@shared_task(bind=True, max_retries=3, retry_backoff=True)
def send_email_task(self, subject, message, from_email, recipient_list, html_message=None):
    """Задача для отправки email с поддержкой HTML."""
    logger.debug(f"Attempting to send email to {recipient_list} from {from_email} with subject: {subject}")
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
        logger.error(f"Failed to send email to {recipient_list}: {str(e)}", exc_info=True)
        self.retry(countdown=60, exc=e)