import pytest
from pydantic import TypeAdapter

from openklant2.factories.klant_contact import CreateKlantContactDataFactory
from openklant2.factories.onderwerp_object import CreateOnderwerpObjectDataFactory
from openklant2.types.pagination import PaginatedResponseBody
from openklant2.types.resources.onderwerp_object import (
    CreateOnderwerpObjectData,
    CreateOnderwerpObjectDataValidator,
    OnderwerpObject,
    OnderwerpObjectValidator,
)


@pytest.fixture()
def een_klant_contact(client):
    data = CreateKlantContactDataFactory()
    return client.klant_contact.create(data=data)


@pytest.fixture()
def een_ander_klant_contact(client):
    data = CreateKlantContactDataFactory()
    return client.klant_contact.create(data=data)


@pytest.fixture()
def klant_contact_factory(client):
    def factory(*args, **kwargs):
        data = CreateKlantContactDataFactory(*args, **kwargs)
        return client.klant_contact.create(data=data)

    return factory


@pytest.fixture()
def een_onderwerp_object(client):
    data = CreateKlantContactDataFactory()
    return client.klant_contact.create(data=data)


@pytest.fixture()
def onderwerp_object_factory(client, klant_contact_factory):
    def factory():
        klant_contact = klant_contact_factory()
        nog_een_klant_contact = klant_contact_factory()
        data = CreateOnderwerpObjectDataFactory(
            klantcontact={"uuid": klant_contact["uuid"]},
            wasKlantcontact={"uuid": nog_een_klant_contact["uuid"]},
        )
        return client.onderwerp_object.create(data=data)

    return factory


@pytest.mark.vcr
def test_create_onderwerp_object(client, een_klant_contact, een_ander_klant_contact):
    data: CreateOnderwerpObjectData = {
        "klantcontact": {"uuid": een_klant_contact["uuid"]},
        "wasKlantcontact": {"uuid": een_ander_klant_contact["uuid"]},
    }
    CreateOnderwerpObjectDataValidator.validate_python(data)
    resp = client.onderwerp_object.create(data=data)

    OnderwerpObjectValidator.validate_python(resp)


@pytest.mark.vcr
def test_list_onderwerp_objecten(client, onderwerp_object_factory):
    onderwerp_objecten = [onderwerp_object_factory() for _ in range(5)]

    resp = client.onderwerp_object.list()
    TypeAdapter(PaginatedResponseBody[OnderwerpObject]).validate_python(resp)

    assert {result["uuid"] for result in resp["results"]} == {
        oo["uuid"] for oo in onderwerp_objecten
    }
