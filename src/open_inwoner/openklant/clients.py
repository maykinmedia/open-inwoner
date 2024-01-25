import logging
from typing import Optional

from ape_pie.client import APIClient
from zgw_consumers.client import build_client as _build_client

from open_inwoner.utils.api import JSONParserClient

from .models import OpenKlantConfig

logger = logging.getLogger(__name__)


def build_client(type_) -> Optional[APIClient]:
    config = OpenKlantConfig.get_solo()
    services = {
        "klanten",
        "contactmomenten",
    }
    if type_ in services:
        service = getattr(config, f"{type_}_service")
        if service:
            client = _build_client(service, client_factory=JSONParserClient)
            return client

    logger.warning(f"no service defined for {type_}")
    return None
