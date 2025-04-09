import pytest
from pydantic import TypeAdapter

from openklant2.types.pagination import PaginatedResponseBody
from openklant2.types.resources import Partij
from openklant2.types.resources.partij_identificator import (
    CreatePartijIdentificatorDataValidator,
    PartijIdentificator,
    PartijIdentificatorValidator,
)


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
def een_andere_organisatie(client):
    data = {
        "digitaleAdressen": None,
        "voorkeursDigitaalAdres": None,
        "rekeningnummers": None,
        "voorkeursRekeningnummer": None,
        "indicatieGeheimhouding": False,
        "indicatieActief": True,
        "voorkeurstaal": "tiv",
        "soortPartij": "organisatie",
        "partijIdentificatie": {"naam": "Andere Test Organisatie"},
    }
    return client.partij.create_organisatie(data=data)


@pytest.fixture()
def een_partij_identificator(client, een_persoon) -> Partij:
    data = {
        "identificeerdePartij": {"uuid": een_persoon["uuid"]},
        "partijIdentificator": {
            "codeObjecttype": "natuurlijk_persoon",
            "codeSoortObjectId": "bsn",
            "objectId": "631706549",
            "codeRegister": "brp",
        },
        "anderePartijIdentificator": "optional_identifier_123",
    }
    return client.partij_identificator.create(data=data)


@pytest.fixture()
def een_kvk_partij_identificator(client, een_organisatie) -> Partij:
    data = {
        "identificeerdePartij": {"uuid": een_organisatie["uuid"]},
        "partijIdentificator": {
            "codeObjecttype": "niet_natuurlijk_persoon",
            "codeSoortObjectId": "kvk_nummer",
            "objectId": "68750110",
            "codeRegister": "hr",
        },
        "anderePartijIdentificator": "optional_identifier_123",
    }
    return client.partij_identificator.create(data=data)


@pytest.mark.vcr
def test_create_partij_identificator(client, een_persoon) -> None:
    data = CreatePartijIdentificatorDataValidator.validate_python(
        {
            "identificeerdePartij": {"uuid": een_persoon["uuid"]},
            "partijIdentificator": {
                "codeObjecttype": "natuurlijk_persoon",
                "codeSoortObjectId": "bsn",
                "objectId": "631706549",
                "codeRegister": "brp",
            },
            "anderePartijIdentificator": "optional_identifier_123",
        }
    )
    resp = client.partij_identificator.create(
        data=data,
    )

    PartijIdentificatorValidator.validate_python(resp)


@pytest.mark.vcr
def test_create_vestiging_identificator(
    client, een_kvk_partij_identificator, een_andere_organisatie
) -> None:
    data = CreatePartijIdentificatorDataValidator.validate_python(
        {
            "identificeerdePartij": {"uuid": een_andere_organisatie["uuid"]},
            "partijIdentificator": {
                "codeObjecttype": "natuurlijk_persoon",
                "codeSoortObjectId": "bsn",
                "objectId": "631706549",
                "codeRegister": "brp",
            },
            "anderePartijIdentificator": "optional_identifier_123",
            "subIdentificatorVan": {
                "uuid": een_kvk_partij_identificator["uuid"],
            },
        }
    )
    resp = client.partij_identificator.create(
        data=data,
    )

    PartijIdentificatorValidator.validate_python(resp)


@pytest.mark.usefixtures("een_partij_identificator")
@pytest.mark.vcr
def test_list_partij_identificator(client) -> None:
    resp = client.partij_identificator.list()
    TypeAdapter(PaginatedResponseBody[PartijIdentificator]).validate_python(resp)


@pytest.mark.vcr
def test_retrieve_partij_identificator(client, een_partij_identificator) -> None:
    resp = client.partij_identificator.retrieve(een_partij_identificator["uuid"])
    TypeAdapter(PartijIdentificator).validate_python(resp)
