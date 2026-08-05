from django.core.exceptions import ImproperlyConfigured

import structlog
from celery_once import QueueOnce

from open_inwoner.accounts.models import User
from open_inwoner.celery import app
from open_inwoner.openklant.constants import KlantenServiceType
from open_inwoner.openklant.models import KlantenSysteemConfig
from open_inwoner.openklant.services import eSuiteVragenService

logger = structlog.stdlib.get_logger(__name__)


@app.task(
    base=QueueOnce,
    once={"keys": ["user_id"], "graceful": True},
)
def warm_klantcontactmomenten_cache_for_user(user_id: int) -> None:
    """
    Warm the eSuite klantcontactmomenten listing cache for a user on login.

    Populates the same cache "Mijn vragen" reads from
    (`ContactmomentenClient.list_klantcontactmomenten_for_klant`), so that page gets
    a cache hit per klant instead of a listing request. OpenKlant2 has no equivalent
    task: its partij uuid is cached directly where it's resolved, with no separate
    listing step to warm.
    """
    log = logger.bind(user_id=user_id)

    config = KlantenSysteemConfig.get_solo()
    if config.primary_backend != KlantenServiceType.ESUITE.value:
        log.info(
            "Skipping klantcontactmomenten cache warm-up: eSuite is not the primary backend",
            primary_backend=config.primary_backend,
        )
        return

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        log.info("Skipping klantcontactmomenten cache warm-up: user no longer exists")
        return

    try:
        service = eSuiteVragenService()
    except ImproperlyConfigured:
        log.info(
            "Skipping klantcontactmomenten cache warm-up: eSuiteVragenService configuration missing"
        )
        return

    fetch_params = service.get_fetch_parameters(user)
    if not fetch_params:
        log.info(
            "Skipping klantcontactmomenten cache warm-up: user has no bsn or kvk to fetch on"
        )
        return

    service.warm_klantcontactmomenten_cache(**fetch_params)
    log.info("Warmed klantcontactmomenten cache")
