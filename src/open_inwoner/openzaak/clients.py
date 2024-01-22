import logging
from typing import Optional

from ape_pie.client import APIClient
from zgw_consumers.client import build_client as _build_client

from .models import OpenZaakConfig

logger = logging.getLogger(__name__)


def build_client(type_) -> Optional[APIClient]:
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
            client = _build_client(service)
            return client
        else:
            logger.warning(f"no service defined for {type_}")
    return None
