import logging
from typing import Optional

from zgw_consumers.models import Service

from .baseclient import BaseClient
from .models import OpenZaakConfig

logger = logging.getLogger(__name__)


class ZGWClients:
    """
    holder for the clients for the different ZGW services

    note the structure is particular because we want lazy initialisation,
    while being able to call .close() (hence not a simple @cached_property)
    additionally for testing it is useful we can run parts of this without all services being mocked
    """

    _zaak: BaseClient = None
    _catalogi: BaseClient = None
    _document: BaseClient = None

    _zaak_service: Optional[Service] = None
    _catalogi_service: Optional[Service] = None
    _document_service: Optional[Service] = None

    def __init__(self):
        config = OpenZaakConfig.get_solo()
        self._zaak_service = config.zaak_service
        self._catalogi_service = config.catalogi_service
        self._document_service = config.document_service

    @property
    def zaak(self) -> BaseClient:
        if not self._zaak:
            self._zaak = BaseClient(self._zaak_service)
        return self._zaak

    @property
    def catalogi(self) -> BaseClient:
        if not self._catalogi:
            self._catalogi = BaseClient(self._catalogi_service)
        return self._catalogi

    @property
    def document(self) -> BaseClient:
        if not self._document:
            self._document = BaseClient(self._document_service)
        return self._document

    def close(self):
        for client in (self._zaak, self._catalogi, self._document):
            if client:
                client.close()
