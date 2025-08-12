import pytest
from pydantic import TypeAdapter

from openklant2.factories.digitaal_adres import DigitaalAdresCreateDataFactory
from openklant2.factories.partij import CreatePartijPersoonDataFactory
from openklant2.types.pagination import PaginatedResponseBody
from openklant2.types.resources import Partij
from openklant2.types.resources.digitaal_adres import (
    DigitaalAdres,
    DigitaalAdresCreateDataValidator,
    DigitaalAdresValidator,
)


@pytest.fixture()
def een_partij(client) -> Partij:
    data = CreatePartijPersoonDataFactory()
    return client.partij.create_persoon(data=data)


@pytest.fixture()
def een_digitaal_adres(client, een_partij) -> Partij:
    data = DigitaalAdresCreateDataFactory(
        verstrektDoorBetrokkene=None,
        verstrektDoorPartij__uuid=een_partij["uuid"],
    )
    return client.digitaal_adres.create(data=data)


@pytest.mark.vcr
def test_create_digitaal_adres(client, een_partij) -> None:
    data = DigitaalAdresCreateDataValidator.validate_python(
        {
            "adres": "foo@bar.com",
            "omschrijving": "professional",
            "soortDigitaalAdres": "email",
            "verstrektDoorBetrokkene": None,
            "verstrektDoorPartij": {"uuid": een_partij["uuid"]},
        }
    )
    resp = client.digitaal_adres.create(
        data=data,
    )

    DigitaalAdresValidator.validate_python(resp)


@pytest.mark.usefixtures("een_digitaal_adres")
@pytest.mark.vcr
def test_list_digitaal_adres(client) -> None:
    resp = client.digitaal_adres.list()
    TypeAdapter(PaginatedResponseBody[DigitaalAdres]).validate_python(resp)


@pytest.mark.vcr
def test_retrieve_digitaal_adres(client, een_digitaal_adres) -> None:
    resp = client.digitaal_adres.retrieve(een_digitaal_adres["uuid"])
    TypeAdapter(DigitaalAdres).validate_python(resp)
