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
def test_list_betrokkenen(client):
    res = client.betrokkene.list(params={"page": 1})

    assert res


@the_vcr.use_cassette
def test_fetch_betrokkene(client):
    res = client.betrokkene.fetch("b89c7aa6-1f94-44f9-afab-da90a73a69d4")

    assert res


@the_vcr.use_cassette
def test_create_betrokkene(client):
    res = client.betrokkene.create(
        data={
            "wasPartij": None,
            "hadKlantcontact": {
                "uuid": "33549ba5-95f0-44d2-9c63-776ec126bc55",
            },
            "rol": "klant",
            "initiator": True,
        }
    )

    assert res


@the_vcr.use_cassette
def test_update_betrokkene(client):
    res = client.betrokkene.update(
        uuid="b89c7aa6-1f94-44f9-afab-da90a73a69d4",
        data={
            "wasPartij": None,
            "hadKlantcontact": {
                "uuid": "33549ba5-95f0-44d2-9c63-776ec126bc55",
            },
            "rol": "klant",
            "initiator": True,
            "bezoekadres": {
                "nummeraanduidingId": 42,
                "adresregel1": "straat",
                "adresregel2": "woonplaats",
                "adresregel3": "",
                "land": "",
            },
        },
    )

    assert res


@the_vcr.use_cassette
def test_partial_update_betrokkene(client):
    res = client.betrokkene.partial_update(
        uuid="b89c7aa6-1f94-44f9-afab-da90a73a69d4",
        data={
            "bezoekadres": {
                "nummeraanduidingId": 42,
                "adresregel1": "straat",
                "adresregel2": "woonplaats",
                "adresregel3": "",
                "land": "",
            }
        },
    )

    assert res


#
# Error flows
#
@the_vcr.use_cassette
def test_create_betrokkene_with_bad_request_exception(client):
    with pytest.raises(BadRequest) as exc_info:
        client.betrokkene.create(
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
                "name": "wasPartij",
                "code": "required",
                "reason": "Dit veld is vereist.",
            },
            {
                "name": "hadKlantcontact",
                "code": "required",
                "reason": "Dit veld is vereist.",
            },
            {
                "name": "rol",
                "code": "required",
                "reason": "Dit veld is vereist.",
            },
            {
                "name": "initiator",
                "code": "required",
                "reason": "Dit veld is vereist.",
            },
        ],
    )

    assert got == want


def test_update_betrokkene_with_bad_request_exception(client):
    with pytest.raises(BadRequest) as exc_info:
        client.betrokkene.update(
            uuid="b89c7aa6-1f94-44f9-afab-da90a73a69d4",
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
                "name": "wasPartij",
                "code": "required",
                "reason": "Dit veld is vereist.",
            },
            {
                "name": "hadKlantcontact",
                "code": "required",
                "reason": "Dit veld is vereist.",
            },
            {
                "name": "rol",
                "code": "required",
                "reason": "Dit veld is vereist.",
            },
            {
                "name": "initiator",
                "code": "required",
                "reason": "Dit veld is vereist.",
            },
        ],
    )

    assert got == want
