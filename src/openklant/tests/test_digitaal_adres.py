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
def test_list_adressen(client):
    res = client.digitaal_adres.list(params={"page": 1})

    assert res


@the_vcr.use_cassette
def test_fetch_adres(client):
    res = client.digitaal_adres.fetch("dbcf1f84-06bd-4320-b4ca-ed066f335038")

    assert res


@the_vcr.use_cassette
def test_create_adres(client):
    res = client.digitaal_adres.create(
        data={
            "verstrektDoorBetrokkene": None,
            "verstrektDoorPartij": None,
            "adres": "test",
            "soortDigitaalAdres": "test",
            "omschrijving": "test",
        }
    )

    assert res


@the_vcr.use_cassette
def test_update_adres(client):
    res = client.digitaal_adres.update(
        uuid="dbcf1f84-06bd-4320-b4ca-ed066f335038",
        data={
            "verstrektDoorBetrokkene": None,
            "verstrektDoorPartij": None,
            "adres": "updated",
            "soortDigitaalAdres": "updated",
            "omschrijving": "updated",
        },
    )

    assert res


@the_vcr.use_cassette
def test_partial_update_adres(client):
    res = client.digitaal_adres.partial_update(
        uuid="dbcf1f84-06bd-4320-b4ca-ed066f335038",
        data={},
    )

    assert res


#
# Error flows
#
@the_vcr.use_cassette
def test_create_adres_with_bad_request_exception(client):
    with pytest.raises(BadRequest) as exc_info:
        client.digitaal_adres.create(
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
                "name": "verstrektDoorBetrokkene",
                "code": "required",
                "reason": "Dit veld is vereist.",
            },
            {
                "name": "verstrektDoorPartij",
                "code": "required",
                "reason": "Dit veld is vereist.",
            },
            {
                "name": "adres",
                "code": "required",
                "reason": "Dit veld is vereist.",
            },
            {
                "name": "soortDigitaalAdres",
                "code": "required",
                "reason": "Dit veld is vereist.",
            },
            {
                "name": "omschrijving",
                "code": "required",
                "reason": "Dit veld is vereist.",
            },
        ],
    )

    assert got == want


def test_update_adres_with_bad_request_exception(client):
    with pytest.raises(BadRequest) as exc_info:
        client.digitaal_adres.update(
            uuid="dbcf1f84-06bd-4320-b4ca-ed066f335038",
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
                "name": "verstrektDoorBetrokkene",
                "code": "required",
                "reason": "Dit veld is vereist.",
            },
            {
                "name": "verstrektDoorPartij",
                "code": "required",
                "reason": "Dit veld is vereist.",
            },
            {
                "name": "adres",
                "code": "required",
                "reason": "Dit veld is vereist.",
            },
            {
                "name": "soortDigitaalAdres",
                "code": "required",
                "reason": "Dit veld is vereist.",
            },
            {
                "name": "omschrijving",
                "code": "required",
                "reason": "Dit veld is vereist.",
            },
        ],
    )

    assert got == want
