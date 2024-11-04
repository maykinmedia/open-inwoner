import pytest
from pydantic import TypeAdapter

from openklant2.factories.klant_contact import CreateKlantContactDataFactory
from openklant2.types.pagination import PaginatedResponseBody
from openklant2.types.resources.klant_contact import (
    CreateKlantContactDataValidator,
    KlantContact,
    KlantContactValidator,
)


@pytest.fixture()
def een_klant_contact(client):
    data = CreateKlantContactDataFactory()
    return client.klant_contact.create(data=data)


@pytest.fixture()
def klant_contact_factory(client):
    def factory(*args, **kwargs):
        data = CreateKlantContactDataFactory(*args, **kwargs)
        return client.klant_contact.create(data=data)

    return factory


@pytest.mark.vcr
def test_create_klant_contact(client) -> None:
    data = CreateKlantContactDataValidator.validate_python(
        {
            "kanaal": "contactformulier",
            "onderwerp": "vraag",
            "inhoud": "Dit is een vraag",
            "taal": "nld",
            "vertrouwelijk": True,
        }
    )
    resp = client.klant_contact.create(data=data)

    KlantContactValidator.validate_python(resp)


@pytest.mark.vcr
def test_retrieve_klant_contact(client, een_klant_contact) -> None:
    resp = client.klant_contact.retrieve(een_klant_contact["uuid"])
    KlantContactValidator.validate_python(resp)


@pytest.mark.vcr
def test_list_klant_contacten(client, een_klant_contact) -> None:
    resp = client.klant_contact.list()
    TypeAdapter(PaginatedResponseBody[KlantContact]).validate_python(resp)
    assert [kc["uuid"] for kc in resp["results"]] == [een_klant_contact["uuid"]]


@pytest.mark.vcr
@pytest.mark.parametrize(
    "true",
    (True, "True", "true", "TRUE"),
)
@pytest.mark.parametrize(
    "false",
    (False, "False", "false", "FALSE", None),
)
def test_list_klant_contacten_with_boolean_filter_params(
    client, klant_contact_factory, true, false
) -> None:
    klant_contact = klant_contact_factory(indicatieContactGelukt=False)

    resp = client.klant_contact.list(
        params={
            "page": 1,
            "indicatieContactGelukt": false,
        }
    )
    TypeAdapter(PaginatedResponseBody[KlantContact]).validate_python(resp)
    assert [kc["uuid"] for kc in resp["results"]] == [klant_contact["uuid"]]

    resp = client.klant_contact.list(
        params={
            "page": 1,
            "indicatieContactGelukt": true,
        }
    )
    TypeAdapter(PaginatedResponseBody[KlantContact]).validate_python(resp)
    assert resp == {"next": None, "previous": None, "count": 0, "results": []}
