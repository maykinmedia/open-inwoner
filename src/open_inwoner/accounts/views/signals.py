import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from open_inwoner.accounts.models import User
from open_inwoner.openklant.clients import build_klanten_client

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_klant_for_new_user(
    sender: type, instance: User, created: bool, **kwargs
) -> None:
    if not created:
        return

    user = instance

    if not user.bsn:
        logger.info("Did not create klant for user %s because of missing bsn", user)
        return

    if not (client := build_klanten_client()):
        logger.warning("Failed to create klanten client for new user %s", user)
        return

    if not (klant := client.create_klant(user_bsn=user.bsn)):
        logger.error("Failed to create klant for new user %s", user)
        return

    logger.info("Created klant %s for new user %s", klant, user)
