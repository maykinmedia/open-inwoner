from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext as _

from open_inwoner.utils.logentry import user_action

MESSAGE_TYPE = {
    "admin": _("user was logged in via admin page"),
    "frontend_email": _("user was logged in via frontend using email"),
    "frontend_digid": _("user was logged in via frontend using digid"),
    "logout": _("user was logged out"),
}


@receiver(user_logged_in)
def log_user_login(sender, user, request, *args, **kwargs):
    current_path = request.path

    if current_path == reverse("admin:login"):
        user_action(request, user, MESSAGE_TYPE["admin"])
    elif current_path == reverse("digid:acs"):
        user_action(request, user, MESSAGE_TYPE["frontend_digid"])
    else:
        user_action(request, user, MESSAGE_TYPE["frontend_email"])


@receiver(user_logged_out)
def log_user_logout(sender, user, request, *args, **kwargs):
    if user:
        user_action(request, user, MESSAGE_TYPE["logout"])
