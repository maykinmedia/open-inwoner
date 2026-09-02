import io

from django.conf import settings
from django.core.management import call_command

import structlog
from celery_once import QueueOnce
from zgw_consumers.api_models.base import factory

from notifications.exceptions import (
    NotificationAlreadyProcessedError,
    NotificationRecordLockError,
    NotificationSkippedException,
)
from notifications.models import NotificationRecord
from open_inwoner.accounts.user_identification import (
    BSNIdentification,
    KVKIdentification,
    UserIdentification,
)
from open_inwoner.celery import app
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.openzaak.api_models import Notification, Zaak
from open_inwoner.openzaak.clients import CatalogiClient, ZakenClient
from open_inwoner.openzaak.metrics import (
    webhook_processing_failures,
    webhook_processing_skipped,
)
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.notifications import handle_zaken_notification
from open_inwoner.openzaak.services import ZGWService
from open_inwoner.utils.concurrency import TimedParallel

logger = structlog.stdlib.get_logger(__name__)


@app.task
def import_zgw_data():
    logger.info("starting import_zgw_data() task")

    out = io.StringIO()

    call_command("zgw_import_data", stdout=out)

    logger.info("finished import_zgw_data() task")

    return out.getvalue()


@app.task
def process_zaken_notification(record_pk: int):
    logger.info("Started process_zaken_notification() task", record_pk=record_pk)

    try:
        with NotificationRecord.objects.lock_for_processing(record_pk) as record:
            config = SiteConfiguration.get_solo()
            if not config.notifications_cases_enabled:
                logger.info(
                    "Skipping notification processing - case notifications disabled",
                    record_pk=record_pk,
                )
                record.processing_output = (
                    "Case notifications are disabled in configuration"
                )
                record.save(update_fields=["processing_output"])
                raise NotificationSkippedException("Case notifications disabled")

            notification = factory(Notification, record.payload)
            try:
                outcome = handle_zaken_notification(notification)
            except Exception as e:
                webhook_processing_failures.add(
                    1,
                    attributes={
                        "channel": record.kanaal or "unknown",
                        "reason": type(e).__name__,
                    },
                )
                logger.exception(
                    "Unknown error while processing notification", record_pk=record_pk
                )
                raise
            else:
                # record the outcome (e.g. why a notification was ignored, or a
                # summary of what was done) so it's visible on the record itself
                record.processing_output = str(outcome)
                record.save(update_fields=["processing_output"])
    except NotificationRecord.DoesNotExist:
        logger.error(
            "Attempted to process unknown Notification Record",
            record_pk=record_pk,
        )
        raise
    except (NotificationRecordLockError, NotificationAlreadyProcessedError) as e:
        # Already locked or processed - don't count as failure (idempotent/concurrent access)
        logger.info(str(e), record_pk=record_pk)
        raise
    except NotificationSkippedException as e:
        # Skipped - not a failure, just disabled
        webhook_processing_skipped.add(
            1,
            attributes={
                "channel": record.kanaal or "unknown",
                "reason": str(e),
            },
        )
        raise


@app.task(
    base=QueueOnce,
    once={
        "keys": ["user_bsn", "user_kvk", "user_rsin", "user_vestigingsnummer"],
        "graceful": True,
    },
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
    raw_result = service.get_raw_zaken(identification)
    raw_zaken = raw_result.zaken

    if not raw_zaken:
        if raw_result.is_incomplete:
            logger.warning(
                "Finished ZGW cache warm-up: raw zaken fetch was incomplete, "
                "unable to determine whether zaken exist"
            )
        else:
            logger.info("Finished ZGW cache warm-up: no zaken found")
        return

    if raw_result.is_incomplete:
        logger.warning(
            "Raw zaken fetch was incomplete during ZGW cache warm-up; "
            "some zaken may not have been found",
            zaken_found=len(raw_zaken),
        )

    # Each thread gets its own zaken client because requests.Session is not
    # thread-safe. Pre-fetch OpenZaakConfig to avoid additional DB calls.
    config = OpenZaakConfig.get_solo()

    with TimedParallel(max_workers=10, name="warm_cache_for_user") as executor:
        futures = {
            executor.submit(
                _warm_single_zaak,
                zaak_with_group.zaak,
                ZGWService._zaken_client_factory(zaak_with_group.api_group, config),
                ZGWService._catalogi_client_factory(zaak_with_group.api_group),
                zaak_with_group.api_group.fetch_eherkenning_zaken_with_rsin,
                identification,
            ): zaak_with_group
            for zaak_with_group in raw_zaken
        }
        result = executor.as_completed(
            futures, cancel_after=settings.ZGW_CACHE_WARMUP_TIMEOUT
        )
        for future in result:
            if exc := future.exception():
                zaak_with_group = futures[future]
                logger.warning(
                    "ZGW cache warm-up failed for zaak",
                    zaak_url=zaak_with_group.zaak.url,
                    exc_info=exc,
                )

    for future in result.cancelled_futures:
        zaak_with_group = futures[future]
        logger.warning(
            "ZGW cache warm-up timed out for zaak",
            zaak_url=zaak_with_group.zaak.url,
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
