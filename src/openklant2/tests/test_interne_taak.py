import pytest
from pydantic import TypeAdapter

from openklant2.factories.actor import CreateActorDataFactory
from openklant2.factories.interne_taak import CreateInterneTaakFactory
from openklant2.factories.klant_contact import CreateKlantContactDataFactory
from openklant2.types.pagination import PaginatedResponseBody
from openklant2.types.resources.interne_taak import (
    CreateInterneTaakDataValidator,
    InterneTaak,
    InterneTaakValidator,
)


@pytest.fixture()
def een_klant_contact(client):
    data = CreateKlantContactDataFactory()
    return client.klant_contact.create(data=data)


@pytest.fixture()
def een_actor(client):
    data = CreateActorDataFactory()
    return client.actor.create(data=data)


@pytest.fixture()
def interne_taak_factory(client, een_klant_contact, een_actor):
    def factory(*args, **kwargs):
        data = CreateInterneTaakFactory(
            *args,
            **kwargs,
            aanleidinggevendKlantcontact={"uuid": een_klant_contact["uuid"]},
            toegewezenAanActor={"uuid": een_actor["uuid"]}
        )
        return client.interne_taak.create(data=data)

    return factory


@pytest.fixture()
def een_interne_taak(interne_taak_factory):
    return interne_taak_factory()


@pytest.mark.vcr
def test_create_interne_taak(client, een_klant_contact, een_actor) -> None:
    data = CreateInterneTaakDataValidator.validate_python(
        {
            "gevraagdeHandeling": "Foobar",
            "aanleidinggevendKlantcontact": {"uuid": een_klant_contact["uuid"]},
            "toegewezenAanActor": {"uuid": een_actor["uuid"]},
            "toelichting": "Dit is een vraag",
            "status": "te_verwerken",
        }
    )
    resp = client.interne_taak.create(data=data)
    InterneTaakValidator.validate_python(resp)


@pytest.mark.vcr
def test_list_interne_taken(client, interne_taak_factory) -> None:
    interne_taken = [interne_taak_factory() for _ in range(5)]
    resp = client.interne_taak.list()

    TypeAdapter(PaginatedResponseBody[InterneTaak]).validate_python(resp)
    assert {result["uuid"] for result in resp["results"]} == {
        it["uuid"] for it in interne_taken
    }


@pytest.mark.vcr
def test_retrieve_interne_taak(client, een_interne_taak) -> None:
    resp = client.interne_taak.retrieve(een_interne_taak["uuid"])

    InterneTaakValidator.validate_python(resp)
    assert resp["uuid"] == een_interne_taak["uuid"]
