from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext as _

from open_inwoner.utils.logentry import user_action


@receiver(user_logged_in)
def log_user_login(sender, user, request, *args, **kwargs):
    if request.path.startswith(reverse("admin:login")):
        user_action(request, user, _("user was logged in via admin page"))
    else:
        user_action(request, user, _("user was logged in via frontend"))


@receiver(user_logged_out)
def log_user_logout(sender, user, request, *args, **kwargs):
    if user:
        user_action(request, user, _("user was logged out"))
