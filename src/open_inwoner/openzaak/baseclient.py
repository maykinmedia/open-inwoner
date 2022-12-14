from typing import Optional

from requests import Session
from zgw_consumers.client import ZGWClient
from zgw_consumers.models import Service


class BaseClient:
    """
    baseclass to wrap a ZGW Service/Client with useful access methods and additional services

    ideally we'd have subclasses for each API, with the fetch_functions as methods,
     but bound-functions are problematic with the cache decorator
    """

    service: Optional[Service] = None

    api: Optional[ZGWClient] = None
    _session: Optional[Session] = None

    def __init__(self, service: Service):
        self.service = service
        if not self.service:
            return

        self.api = service.build_client()

    @property
    def session(self) -> Session:
        # lazy-init
        if self._session:
            return self._session

        # later we'll move to a shared session with connection-pooling, but for now we use it for non-JSON, like documents
        self._session = Session()

        # mirror the authentication setup from ZGW Services and ZDS Client
        if self.api.auth:
            self._session.headers = self.api.auth.credentials()

        if self.service.server_certificate:
            self._session.verify = (
                self.service.server_certificate.public_certificate.path
            )

        if self.service.client_certificate:
            if self.service.client_certificate.private_key:
                self._session.cert = (
                    self.service.client_certificate.public_certificate.path,
                    self.service.client_certificate.private_key.path,
                )
            else:
                self._session.cert = (
                    self.service.client_certificate.public_certificate.path
                )
        return self._session

    def close(self):
        if self._session:
            self._session.close()
