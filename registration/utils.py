from simple_email_confirmation.models import EmailAddress

from email_verification import send_email_verification


def verify_user_emails(user, request, *email_addresses):
    """
    Start email verification process for specified email addresses.

    This should ignore already-verified email addresses.
    """
    for email_address in email_addresses:
        if not EmailAddress.objects.filter(email=email_address).exists():
            email = EmailAddress.objects.create_unconfirmed(email_address, user)
            send_email_verification(email, request)
