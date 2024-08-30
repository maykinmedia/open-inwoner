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
def test_list_actoren(client):
    res = client.actor.list(params={"page": 1})

    assert res


@the_vcr.use_cassette
def test_fetch_actor(client):
    res = client.actor.fetch("f81b8ec7-4b1f-4c42-b1b5-6f686e223005")

    assert res


@the_vcr.use_cassette
def test_create_actor(client):
    res = client.actor.create(
        data={
            "naam": "Hieronymus",
            "soortActor": "medewerker",
        }
    )

    assert res


@the_vcr.use_cassette
def test_update_actor(client):
    res = client.actor.update(
        uuid="f81b8ec7-4b1f-4c42-b1b5-6f686e223005",
        data={
            "naam": "Eric",
            "soortActor": "medewerker",
        },
    )

    assert res["naam"] == "Eric"


@the_vcr.use_cassette
def test_partial_update_actor(client):
    res = client.actor.partial_update(
        uuid="f81b8ec7-4b1f-4c42-b1b5-6f686e223005",
        data={"soortActor": "medewerker", "indicatieActief": False},
    )

    assert res["indicatieActief"] is False


#
# Error flows
#
@the_vcr.use_cassette
def test_create_actor_with_bad_request_exception(client):
    with pytest.raises(BadRequest) as exc_info:
        client.actor.create(
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
                "name": "naam",
                "code": "required",
                "reason": "Dit veld is vereist.",
            },
            {
                "name": "soortActor",
                "code": "required",
                "reason": "Dit veld is vereist.",
            },
        ],
    )

    assert got == want


def test_update_actor_with_bad_request_exception(client):
    with pytest.raises(BadRequest) as exc_info:
        client.actor.update(
            uuid="f81b8ec7-4b1f-4c42-b1b5-6f686e223005",
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
                "name": "naam",
                "code": "required",
                "reason": "Dit veld is vereist.",
            },
            {
                "name": "soortActor",
                "code": "required",
                "reason": "Dit veld is vereist.",
            },
        ],
    )

    assert got == want
