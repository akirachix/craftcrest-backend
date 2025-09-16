from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist
import logging

logger = logging.getLogger(__name__)

def send_otp_email(email, otp, purpose='verify'):
    
    if not email:
        raise ValueError("Email address is required.")
    if purpose not in ['verify', 'reset']:
        raise ValueError("Purpose must be 'verify' or 'reset'.")
    subject = 'Verify Your Email - CraftCrest App' if purpose == 'verify' else 'Reset Your Password - CraftCrest App'
    template = 'emails/verification.html' if purpose == 'verify' else 'emails/forgot_password.html'
    message = f'Your {"verification" if purpose == "verify" else "password reset"} code is: {otp}'
    html_message = None
    try:
        html_message = render_to_string(template, {'otp': otp})
    except TemplateDoesNotExist as e:
        logger.error(f"Template {template} not found, falling back to plain text")
        html_message = None
    logger.debug(f"Sending {purpose} email to {email} with OTP {otp}")
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        html_message=html_message,
        fail_silently=False,
    )
    logger.debug(f"{purpose.capitalize()} email with OTP {otp} sent to {email}")