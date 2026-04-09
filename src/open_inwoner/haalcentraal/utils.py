from django.utils.translation import gettext as _

import structlog

from open_inwoner.haalcentraal.api_models import BRPData
from open_inwoner.haalcentraal.clients import BRPClient
from open_inwoner.utils.logentry import system_action

logger = structlog.stdlib.get_logger(__name__)


def fetch_brp(user_bsn: str) -> BRPData | None:
    if not user_bsn:
        return
    api = BRPClient.from_config()
    return api.fetch_brp(user_bsn)


def update_brp_data_in_db(user, initial=True):
    system_action(
        "Retrieving data for user from haal centraal based on BSN",
        content_object=user,
    )

    brp = fetch_brp(user.bsn)
    if not brp:
        logger.warning("no data retrieved from Haal Centraal")
        return

    brp.copy_to_user(user)
    user.is_prepopulated = True
    user.save()

    system_action(_("data was retrieved from haal centraal"), content_object=user)
