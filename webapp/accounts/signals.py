import logging

from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

logger = logging.getLogger("accounts")


@receiver(user_logged_in)
def on_login(sender, request, user, **kwargs):
    logger.info("Login: %s", user.get_username())


@receiver(user_logged_out)
def on_logout(sender, request, user, **kwargs):
    if user is not None:
        logger.info("Logout: %s", user.get_username())


@receiver(user_login_failed)
def on_login_failed(sender, credentials, request=None, **kwargs):
    logger.warning("Failed login attempt for username %r", credentials.get("username"))
