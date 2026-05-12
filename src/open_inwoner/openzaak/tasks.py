import concurrent.futures
import io

from django.conf import settings
from django.core.management import call_command

import structlog
from celery_once import QueueOnce
from zgw_consumers.api_models.base import factory
from zgw_consumers.concurrent import parallel

from open_inwoner.accounts.user_identification import (
    BSNIdentification,
    KVKIdentification,
    UserIdentification,
)
from open_inwoner.celery import app
from open_inwoner.openzaak.api_models import Notification, Zaak
from open_inwoner.openzaak.clients import CatalogiClient, ZakenClient
from open_inwoner.openzaak.notifications import handle_zaken_notification
from open_inwoner.openzaak.services import ZGWService

logger = structlog.stdlib.get_logger(__name__)


@app.task
def import_zgw_data():
    logger.info("starting import_zgw_data() task")

    out = io.StringIO()

    call_command("zgw_import_data", stdout=out)

    logger.info("finished import_zgw_data() task")

    return out.getvalue()


@app.task
def process_zaken_notification(notification_data: dict):
    logger.info("Started process_zaken_notification() task")
    notification = factory(Notification, notification_data)
    handle_zaken_notification(notification)


@app.task(
    base=QueueOnce,
    once={"keys": ["user_bsn", "user_kvk", "user_vestigingsnummer"], "graceful": True},
)
def warm_cache_for_user(
    user_bsn: str | None = None,
    user_kvk: str | None = None,
    user_rsin: str | None = None,
    user_vestigingsnummer: str | None = None,
):
    """
    Warm the ZGW cache for a user on login.

    Calls the same @cache_result-decorated client methods that the case list and
    detail views use, so those pages get cache hits instead of API round-trips.
    Supports both BSN (DigiD) and KVK (eHerkenning) users.
    """
    if user_bsn:
        identification = BSNIdentification(bsn=user_bsn)
    elif user_kvk:
        identification = KVKIdentification(
            kvk=user_kvk,
            rsin=user_rsin,
            vestigingsnummer=user_vestigingsnummer,
        )
    else:
        return

    logger.info("Starting ZGW cache warm-up")

    service = ZGWService()

    # get_raw_zaken handles multi-group concurrency and timeouts; populates fetch_zaken_by_bsn cache
    raw_zaken = service.get_raw_zaken(identification)
    if not raw_zaken:
        logger.info("Finished ZGW cache warm-up: no zaken found")
        return

    # Pre-build clients per api_group in the main thread so spawned threads only
    # do HTTP requests and never open Django DB connections.
    clients_per_group: dict[int, tuple[ZakenClient, CatalogiClient, bool]] = {}
    for zaak_with_group in raw_zaken:
        group = zaak_with_group.api_group
        if group.pk not in clients_per_group:
            clients_per_group[group.pk] = (
                ZGWService._zaken_client_factory(group),
                ZGWService._catalogi_client_factory(group),
                group.fetch_eherkenning_zaken_with_rsin,
            )

    with parallel(max_workers=10) as executor:
        futures = {
            executor.submit(
                _warm_single_zaak,
                zaak_with_group.zaak,
                *clients_per_group[zaak_with_group.api_group.pk],
                identification,
            ): zaak_with_group
            for zaak_with_group in raw_zaken
        }
        done, timed_out = concurrent.futures.wait(
            futures, timeout=settings.ZGW_CACHE_WARMUP_TIMEOUT
        )

    for future in timed_out:
        zaak_with_group = futures[future]
        logger.warning(
            "ZGW cache warm-up timed out for zaak",
            zaak_url=zaak_with_group.zaak.url,
        )

    for future in done:
        if exc := future.exception():
            zaak_with_group = futures[future]
            logger.warning(
                "ZGW cache warm-up failed for zaak",
                zaak_url=zaak_with_group.zaak.url,
                exc_info=exc,
            )

    logger.info("Finished ZGW cache warm-up")


def _warm_single_zaak(
    zaak: Zaak,
    zaken_client: ZakenClient,
    catalogi_client: CatalogiClient,
    use_rsin: bool,
    identification: UserIdentification,
) -> None:
    # Case list: zaaktype
    if isinstance(zaak.zaaktype, str):
        catalogi_client.fetch_single_zaaktype(zaak.zaaktype)

    # Case list: status + statustype
    if isinstance(zaak.status, str):
        status = zaken_client.fetch_single_status(zaak.status)
        catalogi_client.fetch_single_status_type(status.statustype)

    # Case list: resultaat + resultaattype
    if isinstance(zaak.resultaat, str):
        resultaat = zaken_client.fetch_single_result(zaak.resultaat)
        catalogi_client.fetch_single_resultaat_type(resultaat.resultaattype)

    # Case detail: access check (fetch_single_zaak + fetch_zaak_roles via fetch_rollen_for_user)
    zaken_client.fetch_single_zaak(str(zaak.uuid))
    zaken_client.fetch_rollen_for_user(zaak.url, identification, use_rsin=use_rsin)

    # Case detail: status history
    zaken_client.fetch_status_history(zaak.url)
