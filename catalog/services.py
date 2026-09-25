from django.conf import settings
from django.core.mail import send_mail

from store_settings.models import StoreSettings


def send_tailoring_notification(appointment):
    """Send the existing best-effort tailoring notification.

    Keeping this side effect in one service lets the HTML form and the API
    create appointments with the same behavior.
    """
    store_email = StoreSettings.load().business_email or settings.DEFAULT_STORE_EMAIL
    try:
        send_mail(
            subject=f"New tailoring appointment request from {appointment.full_name}",
            message=(
                f"Service: {appointment.get_service_type_display()}\n"
                f"Preferred date: {appointment.preferred_date or 'Any'} "
                f"{appointment.preferred_time}\n"
                f"Needed by: {appointment.completion_date or 'Not specified'}\n"
                f"Phone: {appointment.phone_number}\n"
                f"Email: {appointment.email}\n\n"
                "Measurements (inches): "
                f"{{'chest': {appointment.measurement_chest}, "
                f"'waist': {appointment.measurement_waist}, "
                f"'hip': {appointment.measurement_hip}, "
                f"'shoulder': {appointment.measurement_shoulder}, "
                f"'sleeve': {appointment.measurement_sleeve}, "
                f"'length': {appointment.measurement_length}}}\n"
                f"Notes: {appointment.measurements_notes}\n"
                f"References: {appointment.reference_notes}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[store_email],
            fail_silently=True,
        )
    except Exception:
        # Match the current storefront behavior: email delivery must not
        # prevent a valid appointment from being saved.
        pass