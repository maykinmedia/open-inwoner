from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from open_inwoner.accounts.models import User
from open_inwoner.utils.logentry import action, user_action, system_action


@receiver(user_logged_in)
def log_user_login(sender, user, request, *args, **kwargs):
    if request.path.startswith(reverse("admin:login")):
        user_action(request, request.user, str(_("user was logged in via admin page")))
    else:
        user_action(request, request.user, str(_("user was logged in via frontend")))


@receiver(user_logged_out)
def log_user_logout(sender, user, request, *args, **kwargs):
    if user:
        user_action(request, request.user, str(_("user was logged out")))
    else:
        system_action(str(_("user was logged out")))


@receiver(pre_save, sender=User)
def on_users_deactivation(instance, **kwargs):
    if instance.is_active is False and instance.deactivated_on:
        action(str(_("user deactivated the account")), instance)
