import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from open_inwoner.accounts.models import User
from open_inwoner.openklant.exceptions import KlantenServiceError
from open_inwoner.openklant.models import OpenKlant2Config
from open_inwoner.openklant.services import OpenKlant2Service, eSuiteKlantenService

logger = logging.getLogger(__name__)


# TODO: Should we also try to fetch pre-existing klant for new user and update?
# The klant could have been created by a different service.
@receiver(post_save, sender=User)
def get_or_create_klant_for_new_user(
    sender: type, instance: User, created: bool, **kwargs
) -> None:
    if not created:
        return

    user = instance

    # OpenKlant2
    # TODO: replace with proper config and refactor branching
    use_ok2 = getattr(settings, "OPENKLANT2_ACTIVE", None)
    if use_ok2 and (openklant2_config := OpenKlant2Config.from_django_settings()):
        try:
            service = OpenKlant2Service(config=openklant2_config)
        except KlantenServiceError:
            logger.error("OpenKlant2 service failed to build")
            return

        if not (
            fetch_params := service.get_fetch_parameters(
                user=user, use_vestigingsnummer=True
            )
        ):
            return

        partij, created = service.get_or_create_partij_for_user(
            fetch_params=fetch_params, user=user
        )
        if not partij:
            logger.error("Failed to create partij for new user %s", user)
            return
        elif not created:
            service.update_user_from_partij(partij_uuid=partij.uuid, user=user)

        logger.info("Created partij %s for new user %s", partij, user)

    # eSuite
    try:
        service = eSuiteKlantenService()
    except KlantenServiceError:
        logger.error("eSuiteKlantenService failed to build")
        return

    if not (
        fetch_params := service.get_fetch_parameters(
            user=user, use_vestigingsnummer=True
        )
    ):
        return

    klant, created = service.get_or_create_klant(fetch_params=fetch_params, user=user)
    if not klant:
        logger.error("Failed to create klant for new user %s", user)
        return
    elif not created:
        service.update_user_from_klant(klant, user)

    logger.info("Created klant %s for new user %s", klant, user)
