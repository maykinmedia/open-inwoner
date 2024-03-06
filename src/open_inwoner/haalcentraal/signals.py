import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.models import User

from .utils import update_brp_data_in_db

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def on_bsn_change(instance, **kwargs):
    if (
        instance.bsn
        and not instance.is_prepopulated
        and instance.login_type == LoginTypeChoices.digid
        and getattr(instance, "_process_on_bsn_change_post_save", True)
    ):
        # workaround to not have a post_save-signal loop if we save() again from within this handler
        # note: this used to be a pre_save, but we need a saved user for the timeline log of the BRP access
        instance._process_on_bsn_change_post_save = False

        update_brp_data_in_db(instance)
