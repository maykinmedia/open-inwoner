import logging
from typing import Optional

from zgw_consumers.client import ZGWClient

from .models import OpenKlantConfig

logger = logging.getLogger(__name__)


def build_client(type_) -> Optional[ZGWClient]:
    config = OpenKlantConfig.get_solo()
    services = {
        "klanten",
        "contactmomenten",
    }
    if type_ in services:
        service = getattr(config, f"{type_}_service")
        if service:
            client = service.build_client()
            return client

    logger.warning(f"no service defined for {type_}")
    return None
