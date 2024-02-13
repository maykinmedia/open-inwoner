import logging

from django.db.models.signals import pre_save
from django.dispatch import receiver

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.models import User

from .utils import update_brp_data_in_db

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=User)
def on_bsn_change(instance, **kwargs):
    if (
        instance.bsn
        and instance.is_prepopulated is False
        and instance.login_type == LoginTypeChoices.digid
    ):
        logger.info("Retrieving data for %s from haal centraal based on BSN", instance)

        update_brp_data_in_db(instance)
