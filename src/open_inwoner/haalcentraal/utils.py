import logging
from typing import Optional

from django.conf import settings
from django.utils.translation import gettext as _

from open_inwoner.haalcentraal.api import BRP_1_3, BRP_2_1, BRPAPI
from open_inwoner.haalcentraal.api_models import BRPData
from open_inwoner.utils.logentry import system_action

logger = logging.getLogger(__name__)


def get_brp_api() -> BRPAPI:
    # TODO move BRP_VERSION to haalcentraal singleton
    brp_version = settings.BRP_VERSION
    if brp_version == "1.3":
        return BRP_1_3()
    elif brp_version == "2.0" or brp_version == "2.1":
        return BRP_2_1()
    else:
        raise NotImplementedError(f"no implementation for BRP API '{brp_version}'")


def fetch_brp(user_bsn: str) -> Optional[BRPData]:
    if not user_bsn:
        return
    api = get_brp_api()
    return api.fetch_brp(user_bsn)


def update_brp_data_in_db(user, initial=True):
    brp = fetch_brp(user.bsn)
    if not brp:
        logger.warning("no data retrieved from Haal Centraal")
        return

    brp.copy_to_user(user)
    user.is_prepopulated = True

    if initial is False:
        user.save()

    system_action(_("data was retrieved from haal centraal"), content_object=user)
