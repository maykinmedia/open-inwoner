from datetime import datetime

from ape_pie.client import APIClient
from pydantic import BaseModel
from zgw_consumers.client import build_client
from zgw_consumers.models import Service

from .exceptions import QmaticException
from .models import QmaticConfig

# API DATA DEFINITIONS


class ServiceDict(BaseModel):
    publicId: str
    name: str
    # could be float too in theory, documentation is not specific (it gives an int example)
    duration: int
    additionalCustomerDuration: int
    custom: str | None


class FullServiceDict(ServiceDict):
    active: bool
    publicEnabled: bool
    created: int
    updated: int


class ServiceGroupDict(BaseModel):
    services: list[ServiceDict]


class BranchDict(BaseModel):
    branchPublicId: str
    branchName: str
    serviceGroups: list[ServiceGroupDict]


class BranchDetailDict(BaseModel):
    name: str
    publicId: str
    phone: str | None
    email: str | None
    branchPrefix: str | None

    addressLine1: str | None
    addressLine2: str | None
    addressZip: str | None
    addressCity: str | None
    addressState: str | None
    addressCountry: str | None

    latitude: float | None
    longitude: float | None
    timeZone: str
    fullTimeZone: str
    custom: str | None
    created: int
    updated: int


class Appointment(BaseModel):
    services: list[ServiceDict]
    title: str
    start: datetime
    end: datetime
    created: int
    updated: int
    publicId: str
    branch: BranchDetailDict
    notes: str | None


class NoServiceConfigured(RuntimeError):
    pass


# API CLIENT IMPLEMENTATIONS, per major version of the API


def QmaticClient() -> "Client":
    """
    Create a Qmatic client instance from the database configuration.
    """
    config = QmaticConfig.get_solo()
    assert isinstance(config, QmaticConfig)
    if (service := config.service) is None:
        raise NoServiceConfigured("No Qmatic service defined, aborting!")
    assert isinstance(service, Service)
    return build_client(service, client_factory=Client)


def startswith_version(url: str) -> bool:
    if url.startswith("v1/"):
        return True
    if url.startswith("v2/"):
        return True
    return False


class Client(APIClient):
    """
    Client implementation for Qmatic.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers["Content-Type"] = "application/json"

    def request(self, method: str, url: str, *args, **kwargs):
        # ensure there is a version identifier in the URL
        if not startswith_version(url):
            url = f"v1/{url}"

        response = super().request(method, url, *args, **kwargs)

        if response.status_code == 500:
            error_msg = response.headers.get(
                "error_message", response.content.decode("utf-8")
            )
            raise QmaticException(
                f"Server error (HTTP {response.status_code}): {error_msg}"
            )

        return response

    def list_appointments_for_customer(
        self, customer_externalid: str
    ) -> list[Appointment]:
        endpoint = f"customers/externalId/{customer_externalid}/appointments"
        response = self.get(endpoint)
        if response.status_code == 404:
            return []
        response.raise_for_status()
        return [Appointment(**entry) for entry in response.json()["appointmentList"]]
