import logging

from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.zaken import Zaak

from .models import OpenZaakConfig

logger = logging.getLogger(__name__)


def fetch_cases(user):
    config = OpenZaakConfig.get_solo()

    if not config.service:
        logger.warning("no service defined for Open Zaak")
        return None

    if not user.is_authenticated or user.bsn is None:
        return None

    client = config.service.build_client()
    response = client.list(
        "zaak",
        request_kwargs={
            "headers": {
                "Accept-Crs": "EPSG:4326",
            },
            "params": {
                "rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn": f"{user.bsn}"
            },
        },
    )
    cases = [factory(Zaak, data) for data in response.get("results", [])]

    return cases
