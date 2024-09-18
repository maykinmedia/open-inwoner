import pytest
from pydantic import TypeAdapter

from open_inwoner.ssd.service.jaaropgave.fwi_include_resolved import Actor
from openklant2.factories.actor import CreateActorDataFactory
from openklant2.types.pagination import PaginatedResponseBody
from openklant2.types.resources.actor import ActorValidator, CreateActorDataValidator


@pytest.fixture()
def actor_factory(client):
    def factory(*args, **kwargs):
        data = CreateActorDataFactory(*args, **kwargs)
        return client.actor.create(data=data)

    return factory


@pytest.fixture()
def een_actor(actor_factory):
    return actor_factory()


@pytest.mark.vcr
def test_create_actor(client) -> None:
    data = CreateActorDataValidator.validate_python(
        {
            "naam": "Miranda Peters",
            "soortActor": "medewerker",
            "indicatieActief": True,
            "actoridentificator": {
                "objectId": "6070462185571",
                "codeObjecttype": "exist",
                "codeRegister": "sport",
                "codeSoortObjectId": "style",
            },
        }
    )
    resp = client.actor.create(data=data)

    ActorValidator.validate_python(resp)


@pytest.mark.vcr
def test_list_actoren(client, actor_factory):
    actoren = [actor_factory() for _ in range(5)]
    resp = client.actor.list()

    TypeAdapter(PaginatedResponseBody[Actor]).validate_python(resp)
    assert {result["uuid"] for result in resp["results"]} == {
        actor["uuid"] for actor in actoren
    }


@pytest.mark.vcr
def test_retrieve_actor(client, een_actor):
    resp = client.actor.retrieve(een_actor["uuid"])

    ActorValidator.validate_python(resp)
    assert resp["uuid"] == een_actor["uuid"]


@pytest.mark.vcr
@pytest.mark.parametrize("indicatie_actief", (True, False))
@pytest.mark.parametrize(
    "soort_actor", ("medewerker", "geautomatiseerde_actor", "organisatorische_eenheid")
)
def test_list_actoren_with_boolean_query_params(
    client, actor_factory, indicatie_actief, soort_actor
):
    excluded_actoren = [
        actor_factory(indicatieActief=not indicatie_actief) for _ in range(2)
    ]
    included_actor = actor_factory(
        indicatieActief=indicatie_actief, soortActor=soort_actor
    )
    resp = client.actor.list(
        params={"indicatieActief": indicatie_actief, "soortActor": soort_actor}
    )

    TypeAdapter(PaginatedResponseBody[Actor]).validate_python(resp)
    uuids = {result["uuid"] for result in resp["results"]}
    assert included_actor["uuid"] in uuids
    assert not any(na["uuid"] in uuids for na in excluded_actoren)
