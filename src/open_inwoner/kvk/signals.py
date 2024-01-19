import logging

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils.translation import gettext as _

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.utils.logentry import system_action

from .client import KvKClient

logger = logging.getLogger(__name__)


@receiver(user_logged_in)
def on_kvk_change(sender, user, request, *args, **kwargs):
    if (
        user.kvk
        and user.is_prepopulated is False
        and user.login_type == LoginTypeChoices.eherkenning
        and not user.rsin
    ):
        system_action(
            _("Retrieving data from KvK API based on KVK number"),
            content_object=user,
        )

        client = KvKClient()
        rsin = client.retrieve_rsin_with_kvk(user.kvk)

        if rsin:
            system_action(_("data was retrieved from KvK API"), content_object=user)

            user.rsin = rsin
            user.is_prepopulated = True
            user.save()
