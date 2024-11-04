import pytest
from pydantic import TypeAdapter

from openklant2.factories.betrokkene import BetrokkeneCreateDataFactory
from openklant2.factories.klant_contact import CreateKlantContactDataFactory
from openklant2.factories.partij import CreatePartijPersoonDataFactory
from openklant2.types.pagination import PaginatedResponseBody
from openklant2.types.resources.betrokkene import (
    Betrokkene,
    BetrokkeneCreateDataValidator,
    BetrokkeneValidator,
)
from openklant2.types.resources.partij import Partij


@pytest.fixture()
def een_persoon(client) -> Partij:
    data = {
        "digitaleAdressen": None,
        "voorkeursDigitaalAdres": None,
        "rekeningnummers": None,
        "voorkeursRekeningnummer": None,
        "indicatieGeheimhouding": False,
        "indicatieActief": True,
        "voorkeurstaal": "crp",
        "soortPartij": "persoon",
        "partijIdentificatie": {
            "contactnaam": {
                "voorletters": "Dr.",
                "voornaam": "Test Persoon",
                "voorvoegselAchternaam": "Mrs.",
                "achternaam": "Gamble",
            }
        },
    }
    return client.partij.create_persoon(data=data)


@pytest.fixture()
def een_organisatie(client):
    data = {
        "digitaleAdressen": None,
        "voorkeursDigitaalAdres": None,
        "rekeningnummers": None,
        "voorkeursRekeningnummer": None,
        "indicatieGeheimhouding": False,
        "indicatieActief": True,
        "voorkeurstaal": "tiv",
        "soortPartij": "organisatie",
        "partijIdentificatie": {"naam": "Test Organisatie"},
    }
    return client.partij.create_organisatie(data=data)


@pytest.fixture()
def een_klant_contact(client):
    data = CreateKlantContactDataFactory()
    return client.klant_contact.create(data=data)


@pytest.fixture()
def persoon_factory(client):
    def factory(*args, **kwargs):
        data = CreatePartijPersoonDataFactory(*args, **kwargs)
        return client.partij.create_persoon(data=data)

    return factory


@pytest.fixture()
def klantcontact_factory(client):
    def factory(*args, **kwargs):
        data = CreateKlantContactDataFactory(*args, **kwargs)
        return client.klant_contact.create(data=data)

    return factory


@pytest.fixture()
def betrokkene_factory(client, persoon_factory, klantcontact_factory):
    def factory(*args, **kwargs):
        klantcontact, partij = klantcontact_factory(), persoon_factory()

        data = BetrokkeneCreateDataFactory(
            *args,
            **kwargs,
            hadKlantcontact={"uuid": klantcontact["uuid"]},
            wasPartij={"uuid": partij["uuid"]}
        )
        return client.betrokkene.create(data=data)

    return factory


@pytest.fixture()
def een_betrokkene(betrokkene_factory):
    return betrokkene_factory()


@pytest.mark.vcr
def test_create_betrokkene(client, een_persoon, een_klant_contact) -> None:
    data = BetrokkeneCreateDataValidator.validate_python(
        {
            "rol": "klant",
            "initiator": True,
            "organisatienaam": "foobar",
            "wasPartij": {"uuid": een_persoon["uuid"]},
            "hadKlantcontact": {"uuid": een_klant_contact["uuid"]},
        }
    )
    resp = client.betrokkene.create(data=data)

    BetrokkeneValidator.validate_python(resp)


@pytest.mark.vcr
def test_list_betrokkenen(client, betrokkene_factory):
    betrokkenen = [betrokkene_factory() for _ in range(5)]
    resp = client.betrokkene.list()

    TypeAdapter(PaginatedResponseBody[Betrokkene]).validate_python(resp)
    assert {result["uuid"] for result in resp["results"]} == {
        betrokkene["uuid"] for betrokkene in betrokkenen
    }


@pytest.mark.vcr
def test_retrieve_betrokkene(client, een_betrokkene):
    resp = client.betrokkene.retrieve(een_betrokkene["uuid"])

    BetrokkeneValidator.validate_python(resp)
    assert resp["uuid"] == een_betrokkene["uuid"]


@pytest.mark.vcr
def test_list_betrokkenen_as_pagination_iter(client, betrokkene_factory):
    # We can't specify the pagesize, so we have to use the default 100 to create more than 1 page of data
    betrokkenen = [betrokkene_factory() for _ in range(101)]
    assert client.betrokkene.list()["next"] is not None

    resp = list(client.betrokkene.list_iter())

    TypeAdapter(list[Betrokkene]).validate_python(resp)
    assert sorted(resp, key=lambda b: b["uuid"]) == sorted(
        betrokkenen, key=lambda b: b["uuid"]
    )
