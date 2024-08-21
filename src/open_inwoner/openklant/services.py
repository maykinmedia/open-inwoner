import logging

from open_inwoner.accounts.choices import NotificationChannelChoice
from open_inwoner.accounts.models import User
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.openklant.api_models import Klant
from open_inwoner.openklant.clients import build_klanten_client
from open_inwoner.utils.logentry import system_action

from .wrap import get_fetch_parameters

logger = logging.getLogger(__name__)


def get_or_create_klant_from_request(request):
    if not (client := build_klanten_client()):
        return

    fetch_params = get_fetch_parameters(request)

    if klant := client.retrieve_klant(**fetch_params):
        msg = "retrieved klant for user"
    elif klant := client.create_klant(**fetch_params):
        msg = f"created klant ({klant.klantnummer}) for user"
    else:
        return

    system_action(msg, content_object=request.user)
    return klant


def update_user_from_klant(klant: Klant, user: User):
    update_data = {}

    if klant.telefoonnummer and klant.telefoonnummer != user.phonenumber:
        update_data["phonenumber"] = klant.telefoonnummer

    if klant.emailadres and klant.emailadres != user.email:
        if not User.objects.filter(email__iexact=klant.emailadres).exists():
            update_data["email"] = klant.emailadres

    config = SiteConfiguration.get_solo()
    if config.enable_notification_channel_choice:
        if (
            klant.toestemming_zaak_notificaties_alleen_digitaal is True
            and user.case_notification_channel != NotificationChannelChoice.digital_only
        ):
            update_data[
                "case_notification_channel"
            ] = NotificationChannelChoice.digital_only

        elif (
            klant.toestemming_zaak_notificaties_alleen_digitaal is False
            and user.case_notification_channel
            != NotificationChannelChoice.digital_and_post
        ):
            update_data[
                "case_notification_channel"
            ] = NotificationChannelChoice.digital_and_post
        else:
            # This is a guard against the scenario where a deployment is
            # configured to use an older version of the klanten backend (that
            # is, one that lacks the toestemmingZaakNotificatiesAlleenDigitaal
            # field). In such a scenario, the enable_notification_channel_choice
            # flag really shouldn't be set until the update has completed, but
            # we suspect this is rare. But to validate that assumption, we log
            # an error so we can remedy this in case we're wrong.
            logger.error(
                "SiteConfig.enable_notification_channel_choice should not be set if"
                " toestemmingZaakNotificatiesAlleenDigitaal is not available from the klanten backend"
            )

    if update_data:
        for attr, value in update_data.items():
            setattr(user, attr, value)
        user.save(update_fields=update_data.keys())

        system_action(
            f"updated user from klant API with fields: {', '.join(sorted(update_data.keys()))}",
            content_object=user,
        )
