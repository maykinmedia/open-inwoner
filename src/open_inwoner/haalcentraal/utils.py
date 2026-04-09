from django.conf import settings
from django.utils.translation import gettext as _

import structlog

from open_inwoner.haalcentraal.api_models import BRPData
from open_inwoner.haalcentraal.clients import BRPClient, BRPClient_1_3, BRPClient_2_1
from open_inwoner.utils.logentry import system_action

logger = structlog.stdlib.get_logger(__name__)


def get_brp_api() -> BRPClient:
    # TODO move BRP_VERSION to haalcentraal singleton
    brp_version = settings.BRP_VERSION
    if brp_version == "1.3":
        return BRPClient_1_3()
    elif brp_version == "2.0" or brp_version == "2.1":
        return BRPClient_2_1()
    else:
        raise NotImplementedError(f"no implementation for BRP API '{brp_version}'")


def fetch_brp(user_bsn: str) -> BRPData | None:
    if not user_bsn:
        return
    api = get_brp_api()
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
