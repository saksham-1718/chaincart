import random
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_email(user_email, otp):
    subject = "Your ChainCart verification code"
    message = f"Your ChainCart verification code is: {otp}\n\nThis code expires in 10 minutes."
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user_email], fail_silently=False)


def is_otp_valid(profile, entered_otp):
    if not profile.email_otp or not profile.email_otp_created_at:
        return False
    if profile.email_otp != entered_otp:
        return False
    if timezone.now() - profile.email_otp_created_at > timedelta(minutes=10):
        return False
    return True


def send_order_confirmation_email(user_email, painting_title, price, tx_hash):
    subject = f"Your ChainCart order confirmation — {painting_title}"
    message = (
        f"Thank you for your purchase!\n\n"
        f"Artwork: {painting_title}\n"
        f"Amount: ₹{price}\n"
        f"Blockchain Transaction: {tx_hash}\n\n"
        f"Shipment and tracking details will be shared to you soon. Stay tuned!"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user_email], fail_silently=True)