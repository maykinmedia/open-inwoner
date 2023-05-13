import logging
from typing import Optional

from zgw_consumers.client import ZGWClient

from .models import OpenZaakConfig

logger = logging.getLogger(__name__)


def build_client(type_) -> Optional[ZGWClient]:
    config = OpenZaakConfig.get_solo()
    services = {
        "zaak",
        "catalogi",
        "document",
        "form",
    }
    if type_ in services:
        service = getattr(config, f"{type_}_service")
        if service:
            client = service.build_client()
            return client
        else:
            logger.warning(f"no service defined for {type_}")
    return None
