# listings/tasks.py

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Booking, Payment


@shared_task
def send_payment_confirmation_email(booking_id):
    """
    Send confirmation email after successful payment.
    Runs asynchronously via Celery.
    """
    try:
        booking = Booking.objects.get(booking_id=booking_id)
        subject = "Booking Payment Confirmation"
        message = (
            f"Hello {booking.user.username},\n\n"
            f"Your payment for booking {booking.booking_id} "
            f"at {booking.listing.name} has been confirmed.\n\n"
            "Thank you for booking with us!\n\n"
            "Best regards,\nALX Travel Team"
        )
        recipient_list = [booking.user.email]

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            fail_silently=False,
        )
        return f"Payment confirmation email sent to {booking.user.email}"

    except Booking.DoesNotExist:
        return f"Booking with ID {booking_id} does not exist."


@shared_task
def send_payment_failure_email(booking_id):
    """
    Send email if payment fails or is cancelled.
    """
    try:
        booking = Booking.objects.get(booking_id=booking_id)
        subject = "Booking Payment Failed"
        message = (
            f"Hello {booking.user.username},\n\n"
            f"Unfortunately, your payment for booking {booking.booking_id} "
            f"at {booking.listing.name} has failed or was cancelled.\n\n"
            "Please try again or contact support.\n\n"
            "Best regards,\nALX Travel Team"
        )
        recipient_list = [booking.user.email]

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            fail_silently=False,
        )
        return f"Payment failure email sent to {booking.user.email}"



    except Booking.DoesNotExist:
        return f"Booking with ID {booking_id} does not exist."