from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext as _

from open_inwoner.haalcentraal.models import HaalCentraalConfig
from open_inwoner.haalcentraal.utils import update_brp_data_in_db
from open_inwoner.utils.logentry import user_action

from ..openklant.services import (
    get_or_create_klant_from_request,
    update_user_from_klant,
)
from .choices import LoginTypeChoices

MESSAGE_TYPE = {
    "admin": _("user was logged in via admin page"),
    "frontend_email": _("user was logged in via frontend using email"),
    "frontend_digid": _("user was logged in via frontend using digid"),
    "frontend_oidc": _("user was logged in via frontend using OpenIdConnect"),
    "logout": _("user was logged out"),
}


@receiver(user_logged_in)
def update_user_from_klant_on_login(sender, user, request, *args, **kwargs):
    # This additional guard is mainly to facilitate easier testing, where not
    # all request factories return a full-fledged request object.
    if not hasattr(request, "user"):
        return

    if user.login_type in [LoginTypeChoices.digid, LoginTypeChoices.eherkenning]:
        if klant := get_or_create_klant_from_request(request):
            update_user_from_klant(klant, user)


@receiver(user_logged_in)
def log_user_login(sender, user, request, *args, **kwargs):
    current_path = request.path

    try:
        digid_path = reverse("digid:acs")
    except:  # noqa
        digid_path = ""

    if current_path == reverse("admin:login"):
        user_action(request, user, MESSAGE_TYPE["admin"])
    elif digid_path and current_path == digid_path:
        user_action(request, user, MESSAGE_TYPE["frontend_digid"])
    elif current_path == reverse("oidc_authentication_callback"):
        user_action(request, user, MESSAGE_TYPE["frontend_oidc"])
    else:
        user_action(request, user, MESSAGE_TYPE["frontend_email"])

    # update brp fields when login with digid and brp is configured
    brp_config = HaalCentraalConfig.get_solo()

    if user.login_type == LoginTypeChoices.digid:
        if brp_config.service:
            update_brp_data_in_db(user)


@receiver(user_logged_out)
def log_user_logout(sender, user, request, *args, **kwargs):
    if user:
        user_action(request, user, MESSAGE_TYPE["logout"])
