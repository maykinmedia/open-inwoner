import functools
from typing import Literal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.core.exceptions import ImproperlyConfigured
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.http import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext as _

import requests
import structlog
from axes.signals import user_locked_out

from open_inwoner.accounts.user_identification import (
    BSNIdentification,
    KVKIdentification,
)
from open_inwoner.haalcentraal.clients import BRPClient
from open_inwoner.kvk.client import KvKClient
from open_inwoner.kvk.exceptions import KVKAPIException
from open_inwoner.openklant.constants import KlantenServiceType
from open_inwoner.openklant.exceptions import KlantAPIError
from open_inwoner.openklant.models import KlantenSysteemConfig
from open_inwoner.openklant.services import OpenKlant2Service, eSuiteKlantenService
from open_inwoner.openzaak.tasks import warm_cache_for_user
from open_inwoner.utils.logentry import system_action, user_action

from .metrics import login_failures, logins, logouts, user_lockouts
from .models import User

logger = structlog.stdlib.get_logger(__name__)


def _update_user_from_brp(user: User):
    if not user.bsn:
        raise ValueError("Expected User with BSN")

    system_action(
        "Retrieving data for user from haal centraal based on BSN",
        content_object=user,
    )

    try:
        client = BRPClient.from_config()
    except ImproperlyConfigured:
        logger.warning("no service configured for Haal Centraal")
        return

    try:
        brp = client.fetch_brp_data_for_bsn(user.bsn)
    except Exception:
        logger.exception("unexpected error fetching BRP data")
        return

    if not brp:
        logger.info("no BRP data found for user", user=user)
        return

    user.populate_from_brp(brp)

    system_action(_("data was retrieved from haal centraal"), content_object=user)


MESSAGE_TYPE = {
    "admin": _("user was logged in via admin page"),
    "frontend_email": _("user was logged in via frontend using email"),
    "frontend_digid": _("user was logged in via frontend using digid"),
    "frontend_oidc": _("user was logged in via frontend using OpenIdConnect"),
    "logout": _("user was logged out"),
}


@receiver(user_logged_in)
def update_user_on_login(sender, user, request, *args, **kwargs):
    # This additional guard is mainly to facilitate easier testing, where not
    # all request factories return a full-fledged request object.
    if not hasattr(request, "user"):
        return

    if not (user.is_bsn_user or user.is_eherkenning_user):
        return

    # Sync company details from KvK -- note it's important this runs _before_ syncing
    # to the klanten APIs, because e.g. RSIN or company name will be a required input
    # for certain sync operations.
    if user.is_eherkenning_user:
        try:
            _update_eherkenning_user_from_kvk_api(user=user)
        except KVKAPIException:
            messages.warning(
                request=request,
                message=_(
                    "We're experiencing technical difficulties. "
                    "Your profile information may not be up-to-date."
                ),
            )

    # update brp fields when login with digid and brp is configured
    if user.is_bsn_user and not user.is_prepopulated:
        try:
            _update_user_from_brp(user)
        except Exception:
            logger.exception("unexpected error updating user from BRP on login")

    config = KlantenSysteemConfig.get_solo()
    if config.primary_backend == KlantenServiceType.OPENKLANT2.value:
        try:
            service = OpenKlant2Service()
        except Exception:
            logger.warning("OpenKlant2 service failed to build", exc_info=True)
        else:
            _update_user_from_openklant2(user=user, service=service, request=request)
    if config.primary_backend == KlantenServiceType.ESUITE.value:
        try:
            service = eSuiteKlantenService()
        except Exception:
            logger.warning("eSuiteKlantenService failed to build", exc_info=True)
        else:
            _update_user_from_esuite(user=user, service=service, request=request)


def _update_user_from_openklant2(
    user: User, service: OpenKlant2Service, request: None = None
) -> None:
    try:
        partij, created = service.get_or_create_partij_for_user(user)
        if partij and not created:
            service.update_user_from_partij(partij=partij, user=user)

    except Exception:
        logger.exception("Error updating user from partij via OpenKlant2")


def _update_user_from_esuite(
    user: User, service: eSuiteKlantenService, request: None = None
) -> None:
    if not (fetch_params := service.get_fetch_parameters(user)):
        return

    try:
        klant, created = service.get_or_create_klant(
            fetch_params=fetch_params, user=user
        )
        if klant and not created:
            service.update_user_from_klant(klant, user)
    except (KlantAPIError, requests.RequestException):
        logger.error("Error updating user from klant via eSuite")


def _update_eherkenning_user_from_kvk_api(user: User):
    extra_exc_params = {"kvk": user.kvk, "vestiging": user.vestiging}
    kvk_client = KvKClient()
    updated_fields = []

    # Update company name. We want this to run on every login because it may
    # change (if infrequently)
    basisprofiel = kvk_client.get_basisprofiel(kvk=user.kvk)
    company_name = basisprofiel.get("naam")
    if company_name and user.company_name != company_name:
        user.company_name = company_name
        user.save(update_fields=["company_name"])
        updated_fields.append("company_name")

    # Update branch name (leave empty for rechtspersoon)
    if user.vestiging:
        branch_profile = kvk_client.get_vestigingsprofiel(vestiging=user.vestiging)
        branch_name = branch_profile.get("eersteHandelsnaam")
        if branch_name and user.branch_name != branch_name:
            user.branch_name = branch_name
            user.save()
            updated_fields.append("branch_name")

    # Optionally update RSIN. Unlike company name, RSIN should be immutable, so we
    # only have to fetch it if it's not set.
    if not user.rsin:
        rsin = kvk_client.retrieve_rsin_with_kvk(kvk=user.kvk)

        if rsin:
            user.rsin = rsin
            user.save(update_fields=["rsin"])
            updated_fields.append("rsin")
        else:
            logger.exception("Unable to sync rsin from KvK API", user=user)

    if updated_fields:
        system_action(
            _(
                "user attributes were updated from KvK API: %(fields)s"
                % {"fields": ", ".join(updated_fields)}
            ),
            content_object=user,
        )


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


@receiver(user_logged_out)
def log_user_logout(sender, user, request, *args, **kwargs):
    if user:
        user_action(request, user, MESSAGE_TYPE["logout"])


@receiver(post_save, sender=User)
def on_bsn_change(instance, **kwargs):
    if (
        instance.is_bsn_user
        and not instance.is_prepopulated
        and getattr(instance, "_process_on_bsn_change_post_save", True)
    ):
        # workaround to not have a post_save-signal loop if we save() again from within this handler
        # note: this used to be a pre_save, but we need a saved user for the timeline log of the BRP access
        instance._process_on_bsn_change_post_save = False

        _update_user_from_brp(instance)


@receiver(pre_save, sender=User)
def save_previous_login(sender, instance, update_fields, **kwargs):
    """Save previous `last_login` value"""

    if update_fields and "last_login" in update_fields:
        old_instance = User.objects.get(id=instance.id)
        instance.previous_login = old_instance.last_login


@receiver(user_logged_in, dispatch_uid="user_logged_in.increment_counter")
def increment_logins_counter(
    sender: type[User], request: HttpRequest | None, user: User, **kwargs
) -> None:
    logins.add(
        1,
        attributes={
            "user_id": user.id,
            "login_type": user.login_type,
            "http_target": request.path if request else "",
        },
    )


@receiver(user_logged_in, dispatch_uid="user_logged_in.warm_zgw_cache")
def warm_zgw_cache_on_login(
    sender: type[User], request: HttpRequest | None, user: User, **kwargs
) -> None:
    dispatch = functools.partial(
        warm_cache_for_user.apply_async, queue=settings.CACHE_SEEDING_QUEUE
    )
    try:
        match user.identification:
            case BSNIdentification(bsn=bsn):
                dispatch(
                    kwargs={
                        "user_bsn": bsn,
                        "user_kvk": None,
                        "user_rsin": None,
                        "user_vestigingsnummer": None,
                    }
                )
            case KVKIdentification(
                kvk=kvk, rsin=rsin, vestigingsnummer=vestigingsnummer
            ):
                dispatch(
                    kwargs={
                        "user_bsn": None,
                        "user_kvk": kvk,
                        "user_rsin": rsin,
                        "user_vestigingsnummer": vestigingsnummer,
                    }
                )
    except Exception:
        logger.warning("Failed to dispatch ZGW cache warm-up task", exc_info=True)


@receiver(user_logged_out, dispatch_uid="user_logged_out.increment_counter")
def increment_logouts_counter(
    sender: type[User], request: HttpRequest | None, user: User | None, **kwargs
) -> None:
    if user is None:
        return
    logouts.add(
        1,
        attributes={
            "user_id": user.id,
            "login_type": user.login_type,
        },
    )


@receiver(user_login_failed, dispatch_uid="user_login_failed.increment_counter")
def increment_login_failure_counter(
    sender, request: HttpRequest | None = None, **kwargs
):
    login_failures.add(
        1,
        attributes={"http_target": request.path if request else ""},
    )


@receiver(user_locked_out, dispatch_uid="user_locked_out.increment_counter")
def increment_user_locked_out_counter(
    sender: Literal["axes"],
    request: HttpRequest,
    username: str,
    ip_address: str,
    **kwargs,
) -> None:
    user_lockouts.add(
        1,
        attributes={
            "http_target": request.path,
            "username": username,
        },
    )
