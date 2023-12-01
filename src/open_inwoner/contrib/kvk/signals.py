import logging

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.translation import gettext as _

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.models import User
from open_inwoner.utils.logentry import system_action

from .client import KvKClient

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=User)
def on_kvk_change(instance, **kwargs):
    if (
        instance.kvk
        and instance.is_prepopulated is False
        and instance.login_type == LoginTypeChoices.eherkenning
        and not instance.rsin
    ):
        system_action(
            _("Retrieving data from KvK API based on KVK number"),
            content_object=instance,
        )

        client = KvKClient()
        rsin = client.retrieve_rsin_with_kvk(instance.kvk)

        if rsin:
            system_action(_("data was retrieved from KvK API"), content_object=instance)

            instance.rsin = rsin
            instance.is_prepopulated = True
