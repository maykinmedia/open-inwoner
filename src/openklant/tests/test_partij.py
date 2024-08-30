import os

import pytest
import vcr
from vcr.record_mode import RecordMode

from openklant.exceptions import BadRequest

current_dir = os.path.dirname(__file__)
cassette_library_dir = os.path.join(current_dir, "fixtures", "cassettes")

the_vcr = vcr.VCR(
    serializer="yaml",
    cassette_library_dir=cassette_library_dir,
    record_mode=RecordMode.ALL,
)


@the_vcr.use_cassette
def test_list_partijen(client):
    resp = client.partij.list(params={"page": 1})

    assert resp


@the_vcr.use_cassette
def test_retrieve_partij(client):
    resp = client.partij.retrieve(
        "d5546623-9be9-4a67-9188-593e5841e3d7",
        params={"expand": ["betrokkenen", "digitaleAdressen"]},
    )

    assert resp


@the_vcr.use_cassette
def test_create_persoon(client):
    resp = client.partij.create_persoon(
        data={
            "soortPartij": "persoon",
            "digitaleAdressen": None,
            "rekeningnummers": None,
            "voorkeursRekeningnummer": None,
            "soortPartij": "persoon",
            "voorkeurstaal": "FOO",
            "indicatieActief": True,
            "indicatieGeheimhouding": False,
            "voorkeursDigitaalAdres": None,
            "partijIdentificatie": {"contactnaam": None},
            "bezoekadres": {},
        },
    )

    assert resp


@the_vcr.use_cassette
def test_create_contactpersoon(client):
    resp = client.partij.create_persoon(
        data={
            "soortPartij": "contactpersoon",
            "digitaleAdressen": None,
            "rekeningnummers": None,
            "voorkeursRekeningnummer": None,
            "voorkeurstaal": "FOO",
            "indicatieActief": True,
            "indicatieGeheimhouding": False,
            "voorkeursDigitaalAdres": None,
            "partijIdentificatie": {"contactnaam": None},
            "bezoekadres": {},
        },
    )

    assert resp


@the_vcr.use_cassette
def test_create_organisatie(client):
    resp = client.partij.create_organisatie(
        data={
            "soortPartij": "organisatie",
            "digitaleAdressen": None,
            "rekeningnummers": None,
            "voorkeursRekeningnummer": None,
            "voorkeurstaal": "FOO",
            "indicatieActief": True,
            "indicatieGeheimhouding": False,
            "voorkeursDigitaalAdres": None,
            "partijIdentificatie": {"contactnaam": None},
            "bezoekadres": {},
        },
    )

    assert resp


@the_vcr.use_cassette
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
    )

    assert got == want
