from django.utils.dateparse import parse_datetime

import structlog
from requests import RequestException

from open_inwoner.celery import app
from open_inwoner.openzaak.exceptions import ZgwAPIError
from open_inwoner.openzaak.models import OpenZaakConfig, ZGWApiGroupConfig
from open_inwoner.openzaak.notifications import (
    _get_initiator_users_from_roles,
    send_case_update_email,
)
from open_inwoner.openzaak.services import ZGWService

from .client import GesprekkenAPIError, build_gesprekken_client, uuid_from_url
from .models import GesprekGezien
from .services import eigen_deelname, resident_email, resolve_partij_uuid

logger = structlog.stdlib.get_logger(__name__)

MAIL_TEMPLATE = "case_gesprek_notification"


@app.task
def send_gesprek_bijdrage_email(gesprek_url: str, zaak_url: str, geleverd_op: str):
    """
    E-mail the residents of the zaak who take part in the gesprek about a new
    bijdrage of the municipality, unless they turned off case notifications or
    have seen the gesprek since the bijdrage was delivered.
    """
    geleverd = parse_datetime(geleverd_op)

    if not (client := build_gesprekken_client()):
        return "ignored: no Gesprekken API configured"
    try:
        gesprek = client.get_gesprek(uuid_from_url(gesprek_url))
    except (GesprekkenAPIError, RequestException):
        logger.exception("Could not retrieve gesprek for e-mail", gesprek=gesprek_url)
        return "ignored: cannot retrieve gesprek"

    try:
        api_group = ZGWApiGroupConfig.objects.resolve_group_from_hints(url=zaak_url)
    except ZGWApiGroupConfig.DoesNotExist:
        return "ignored: no API group configured for zaak"

    service = ZGWService(use_cache=False)
    try:
        roles = service.fetch_zaak_roles(zaak_url, api_group)
        zaak = service.fetch_zaak_by_url(zaak_url, api_group)
        zaak.zaaktype = service.fetch_zaaktype_by_url(zaak.zaaktype, api_group)
    except (ZgwAPIError, RequestException):
        logger.exception("Could not retrieve zaak for gesprek e-mail", zaak=zaak_url)
        return "ignored: cannot retrieve zaak"

    users = _get_initiator_users_from_roles(
        roles,
        api_group=api_group,
        limit_access_to_role=OpenZaakConfig.get_solo().limit_user_visible_cases_to_role,
    )

    sent = 0
    for user in users:
        if not user.cases_notifications:
            continue
        # Someone else with access to the zaak (e.g. a gemachtigde) who does not
        # take part in the gesprek
        if not eigen_deelname(gesprek, resolve_partij_uuid(user)):
            continue
        if GesprekGezien.objects.filter(
            user=user, gesprek_url=gesprek_url, gezien_op__gte=geleverd
        ).exists():
            continue
        if not (email := resident_email(user)):
            continue
        send_case_update_email(user, zaak, MAIL_TEMPLATE, api_group, recipient=email)
        sent += 1

    return f"sent {sent} e-mail(s)"
