import textwrap

import pytest
from pydantic import TypeAdapter

from openklant2.exceptions import BadRequest
from openklant2.factories.partij import (
    CreatePartijContactPersoonDataFactory,
    CreatePartijOrganisatieDataFactory,
    CreatePartijPersoonDataFactory,
)
from openklant2.types import PaginatedResponseBody
from openklant2.types.resources import (
    CreatePartijContactpersoonDataValidator,
    CreatePartijOrganisatieDataValidator,
    CreatePartijPersoonDataValidator,
    Partij,
    PartijValidator,
)


@pytest.fixture()
def een_persoon(client):
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


@pytest.mark.vcr
@pytest.mark.usefixtures("een_persoon", "een_organisatie")
def test_list_partijen(client):
    resp = client.partij.list()

    TypeAdapter(PaginatedResponseBody[Partij]).validate_python(resp)


@pytest.mark.vcr
@pytest.mark.parametrize(
    "expand",
    (
        "betrokkenen",
        "betrokkenen.hadKlantcontact",
        "categorieRelaties",
        "digitaleAdressen",
    ),
)
def test_retrieve_partij(client, een_persoon, expand):
    resp = client.partij.retrieve(
        een_persoon["uuid"],
        params={"expand": [expand]},
    )

    PartijValidator.validate_python(resp)


@pytest.mark.vcr
def test_create_persoon(client) -> None:
    data = CreatePartijPersoonDataValidator.validate_python(
        {
            "soortPartij": "persoon",
            "digitaleAdressen": None,
            "rekeningnummers": None,
            "voorkeursRekeningnummer": None,
            "voorkeurstaal": "nld",
            "indicatieActief": True,
            "indicatieGeheimhouding": False,
            "voorkeursDigitaalAdres": None,
            "partijIdentificatie": {"contactnaam": None},
        }
    )
    resp = client.partij.create_persoon(
        data=data,
    )

    PartijValidator.validate_python(resp)


@pytest.mark.vcr
def test_create_contactpersoon(client, een_organisatie):
    data = CreatePartijContactpersoonDataValidator.validate_python(
        {
            "soortPartij": "contactpersoon",
            "digitaleAdressen": None,
            "rekeningnummers": None,
            "voorkeursRekeningnummer": None,
            "voorkeurstaal": "nld",
            "indicatieActief": True,
            "indicatieGeheimhouding": False,
            "voorkeursDigitaalAdres": None,
            "partijIdentificatie": {
                "contactnaam": None,
                "werkteVoorPartij": {"uuid": een_organisatie["uuid"]},
            },
        }
    )
    resp = client.partij.create_contactpersoon(
        data={
            "soortPartij": "contactpersoon",
            "digitaleAdressen": None,
            "rekeningnummers": None,
            "voorkeursRekeningnummer": None,
            "voorkeurstaal": "nld",
            "indicatieActief": True,
            "indicatieGeheimhouding": False,
            "voorkeursDigitaalAdres": None,
            "partijIdentificatie": {
                "contactnaam": None,
                "werkteVoorPartij": {"uuid": een_organisatie["uuid"]},
            },
        },
    )

    PartijValidator.validate_python(resp)


@pytest.mark.vcr
def test_create_organisatie(client):
    data = CreatePartijOrganisatieDataValidator.validate_python(
        {
            "soortPartij": "organisatie",
            "digitaleAdressen": None,
            "rekeningnummers": None,
            "voorkeursRekeningnummer": None,
            "voorkeurstaal": "nld",
            "indicatieActief": True,
            "indicatieGeheimhouding": False,
            "voorkeursDigitaalAdres": None,
            "partijIdentificatie": {"naam": "AcmeCorp Ltd"},
        }
    )
    resp = client.partij.create_organisatie(
        data=data,
    )

    PartijValidator.validate_python(resp)


@pytest.mark.vcr
def test_create_with_bad_request_exception(client):
    with pytest.raises(BadRequest) as exc_info:
        client.partij.create_organisatie(
            data={},
        )

    got = (
        exc_info.value.status,
        exc_info.value.code,
        exc_info.value.title,
        exc_info.value.invalidParams,
        str(exc_info.value),
    )
    want = (
        400,
        "invalid",
        "Invalid input.",
        [
            {
                "name": "digitaleAdressen",
                "code": "required",
                "reason": "Dit veld is vereist.",
            },
            {
                "name": "voorkeursDigitaalAdres",
                "code": "required",
                "reason": "Dit veld is vereist.",
            },
            {
                "name": "rekeningnummers",
                "code": "required",
                "reason": "Dit veld is vereist.",
            },
            {
                "name": "voorkeursRekeningnummer",
                "code": "required",
                "reason": "Dit veld is vereist.",
            },
            {
                "name": "soortPartij",
                "code": "required",
                "reason": "Dit veld is vereist.",
            },
            {
                "name": "indicatieActief",
                "code": "required",
                "reason": "Dit veld is vereist.",
            },
        ],
        textwrap.dedent(
            """
                status=400 code=400 title="Invalid input.":
                Invalid parameters:
                {'code': 'required',
                 'name': 'digitaleAdressen',
                 'reason': 'Dit veld is vereist.'}
                {'code': 'required',
                 'name': 'voorkeursDigitaalAdres',
                 'reason': 'Dit veld is vereist.'}
                {'code': 'required',
                 'name': 'rekeningnummers',
                 'reason': 'Dit veld is vereist.'}
                {'code': 'required',
                 'name': 'voorkeursRekeningnummer',
                 'reason': 'Dit veld is vereist.'}
                {'code': 'required', 'name': 'soortPartij', 'reason': 'Dit veld is vereist.'}
                {'code': 'required',
                 'name': 'indicatieActief',
                 'reason': 'Dit veld is vereist.'}
            """
        ).strip(),
    )

    assert got == want


@pytest.mark.vcr
def test_partial_update(client, een_persoon):
    target_nummer = "18744"
    target_correspondentieadres = {
        "adresregel1": "foo",
        "adresregel2": "bar",
        "adresregel3": "baz",
        "land": "NL",
        "nummeraanduidingId": "",
    }
    assert een_persoon["nummer"] != target_nummer
    assert een_persoon["correspondentieadres"] != target_correspondentieadres

    resp = client.partij.partial_update(
        een_persoon["uuid"],
        data={
            # TODO: remove soortPartij which shouldn't be required, see:
            # https://github.com/maykinmedia/open-klant/issues/345
            "correspondentieadres": target_correspondentieadres,
            "soortPartij": een_persoon["soortPartij"],
            "nummer": target_nummer,
        },
    )

    PartijValidator.validate_python(resp)
    assert resp["nummer"] == target_nummer
    assert resp["correspondentieadres"] == target_correspondentieadres


def test_factory_partij_persoon_data():
    data = CreatePartijPersoonDataFactory.build()
    CreatePartijPersoonDataValidator.validate_python(data)


def test_factory_partij_organisatie_data():
    data = CreatePartijOrganisatieDataFactory.build()
    CreatePartijOrganisatieDataValidator.validate_python(data)


def test_factory_partij_contactpersoon_data():
    data = CreatePartijContactPersoonDataFactory.build()
    CreatePartijContactpersoonDataValidator.validate_python(data)
