import logging

from .models import OpenZaakConfig

logger = logging.getLogger(__name__)


def build_client(type_):
    config = OpenZaakConfig.get_solo()

    if type_ == "zaak":
        if not config.zaak_service:
            logger.warning("no service defined for Zaak")
            return

        client = config.zaak_service.build_client()

    elif type_ == "catalogi":
        if not config.catalogi_service:
            logger.warning("no service defined for Catalogi")
            return

        client = config.catalogi_service.build_client()

    return client
