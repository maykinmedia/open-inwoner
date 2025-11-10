from django.db.models.signals import post_save
from django.dispatch import receiver

from open_inwoner.accounts.models import User

from .utils import update_brp_data_in_db


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

        update_brp_data_in_db(instance)
