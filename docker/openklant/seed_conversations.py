#!/usr/bin/env python
"""Seed a running Open Klant instance with a handful of question/reply conversations.

Uses `open-klant-client` directly: klantcontacten chained by onderwerpobjecten whose
`wasKlantcontact` points at the klantcontact being replied to.

Most replies register the inwoner as betrokkene, and so are already visible through
the partij-filtered listing that an inwoner's own "mijn vragen" view uses. A few
deliberately don't, the way an external system might -- those can only be found by
asking what replies to a known klantcontact, or by looking a missing parent up
directly by uuid.

Usage (against the stack started by `docker-compose.openklant.yml`, port 8338):

    python docker/openklant/seed_conversations.py

Safe to run more than once: every subject gets a fresh timestamp, so re-running adds
another batch instead of colliding.

Requires `open-klant-client` (already in requirements/base.txt).
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Literal

from openklant_client import OpenKlantClient
from openklant_client.types.resources.klant_contact import KlantContact

# Matches docker/openklant/fixtures/db.json, loaded by the `openklant-seed` compose
# service. Override with --token if yours differs.
DEFAULT_BASE_URL = "http://localhost:8338/klantinteracties/api/v1"
DEFAULT_TOKEN = "9b17346dbb9493f967e6653bbcdb03ac2f7009fa"  # noqa: S105 -- fixture token, not a secret

# BSN of `testuser` in the Keycloak realm (docker/keycloak/fixtures/realm.json), the
# account DigiD-mock login authenticates as. Reuses the partij if one already exists.
DEFAULT_BSN = "111222333"

KANAAL = "contactformulier"
ACTOR_NAAM = "Backoffice (seed_conversations.py)"

InterneTaakStatus = Literal["te_verwerken", "verwerkt"]


def get_or_create_partij(
    client: OpenKlantClient, *, bsn: str, voornaam: str, achternaam: str
) -> str:
    """Return the partij's uuid for `bsn`, creating one if needed."""
    existing = client.partij.list(
        params={
            "partijIdentificator__codeObjecttype": "natuurlijk_persoon",
            "partijIdentificator__codeRegister": "brp",
            "partijIdentificator__codeSoortObjectId": "bsn",
            "partijIdentificator__objectId": bsn,
        }
    )
    if existing["results"]:
        return existing["results"][0]["uuid"]

    partij = client.partij.create_persoon(
        data={
            "soortPartij": "persoon",
            "indicatieActief": True,
            "digitaleAdressen": None,
            "voorkeursDigitaalAdres": None,
            "rekeningnummers": None,
            "voorkeursRekeningnummer": None,
            "voorkeurstaal": "nld",
            "indicatieGeheimhouding": False,
            "partijIdentificatie": {
                "contactnaam": {
                    "voorletters": voornaam[0],
                    "voornaam": voornaam,
                    "voorvoegselAchternaam": "",
                    "achternaam": achternaam,
                }
            },
        }
    )
    client.partij_identificator.create(
        data={
            "identificeerdePartij": {"uuid": partij["uuid"]},
            "partijIdentificator": {
                "codeObjecttype": "natuurlijk_persoon",
                "codeSoortObjectId": "bsn",
                "codeRegister": "brp",
                "objectId": bsn,
            },
        }
    )
    return partij["uuid"]


def get_or_create_actor(client: OpenKlantClient, *, naam: str) -> str:
    """Return the actor's uuid, creating one if needed."""
    existing = client.actor.list(params={"naam": naam})
    if existing["results"]:
        return existing["results"][0]["uuid"]

    actor = client.actor.create(
        data={"naam": naam, "soortActor": "medewerker", "indicatieActief": True}
    )
    return actor["uuid"]


def create_klantcontact(
    client: OpenKlantClient, *, onderwerp: str, inhoud: str
) -> KlantContact:
    return client.klant_contact.create(
        data={
            "kanaal": KANAAL,
            "onderwerp": onderwerp,
            "inhoud": inhoud,
            "taal": "nld",
            "vertrouwelijk": False,
            "plaatsgevondenOp": datetime.now(timezone.utc).isoformat(),
        }
    )


def add_inwoner_betrokkene(
    client: OpenKlantClient, *, klantcontact_uuid: str, partij_uuid: str
) -> None:
    """Register the inwoner as betrokkene.

    What makes a klantcontact show up in the partij-filtered listing at all.
    """
    client.betrokkene.create(
        data={
            "hadKlantcontact": {"uuid": klantcontact_uuid},
            "wasPartij": {"uuid": partij_uuid},
            "rol": "klant",
            "organisatienaam": "",
            "initiator": True,
        }
    )


def add_staff_betrokkene(client: OpenKlantClient, *, klantcontact_uuid: str) -> None:
    """Register a betrokkene that is *not* the inwoner.

    The shape of a reaction registered without the inwoner as betrokkene: invisible
    to the partij-filtered listing, findable only by asking what replies to a known
    klantcontact or looking it up directly by uuid.
    """
    client.betrokkene.create(
        data={
            "hadKlantcontact": {"uuid": klantcontact_uuid},
            "wasPartij": None,
            "rol": "vertegenwoordiger",
            "organisatienaam": "Gemeente (backoffice)",
            "initiator": False,
        }
    )


def link_reply(
    client: OpenKlantClient, *, klantcontact_uuid: str, parent_uuid: str
) -> None:
    """Register `klantcontact_uuid` as a reply to `parent_uuid`."""
    client.onderwerp_object.create(
        data={
            "klantcontact": {"uuid": klantcontact_uuid},
            "wasKlantcontact": {"uuid": parent_uuid},
        }
    )


def link_zaak(
    client: OpenKlantClient, *, klantcontact_uuid: str, zaak_uuid: str
) -> None:
    """Tie a klantcontact to a zaak."""
    client.onderwerp_object.create(
        data={
            "klantcontact": {"uuid": klantcontact_uuid},
            "onderwerpobjectidentificator": {
                "objectId": zaak_uuid,
                "codeObjecttype": "zgw-Zaak",
                "codeRegister": "openzaak",
                "codeSoortObjectId": "uuid",
            },
        }
    )


def add_interne_taak(
    client: OpenKlantClient,
    *,
    klantcontact_uuid: str,
    actor_uuid: str,
    status: InterneTaakStatus,
) -> None:
    client.interne_taak.create(
        data={
            "aanleidinggevendKlantcontact": {"uuid": klantcontact_uuid},
            "toegewezenAanActor": {"uuid": actor_uuid},
            "gevraagdeHandeling": "Vraag beantwoorden in aanleiding gevend klant contact",
            "toelichting": "Seed data (seed_conversations.py)",
            "status": status,
        }
    )


# --- scenarios -----------------------------------------------------------------
# Each returns the subject it used, just so `main` can print a summary.


def seed_open_question(
    client: OpenKlantClient, *, partij_uuid: str, actor_uuid: str, tag: str
) -> str:
    """A question with no reply yet, interne taak still `te_verwerken`."""
    subject = f"Vraag over mijn uitkering [{tag}]"
    question = create_klantcontact(
        client,
        onderwerp=subject,
        inhoud="Ik heb een vraag over de hoogte van mijn uitkering deze maand.",
    )
    add_inwoner_betrokkene(
        client, klantcontact_uuid=question["uuid"], partij_uuid=partij_uuid
    )
    add_interne_taak(
        client,
        klantcontact_uuid=question["uuid"],
        actor_uuid=actor_uuid,
        status="te_verwerken",
    )
    return subject


def seed_answered_question(
    client: OpenKlantClient, *, partij_uuid: str, actor_uuid: str, tag: str
) -> str:
    """A question with a single visible reply, interne taak `verwerkt` (afgehandeld)."""
    subject = f"Klacht over de wachttijd [{tag}]"
    question = create_klantcontact(
        client,
        onderwerp=subject,
        inhoud="Ik wacht al drie weken op een reactie op mijn eerdere melding.",
    )
    add_inwoner_betrokkene(
        client, klantcontact_uuid=question["uuid"], partij_uuid=partij_uuid
    )
    add_interne_taak(
        client,
        klantcontact_uuid=question["uuid"],
        actor_uuid=actor_uuid,
        status="verwerkt",
    )

    answer = create_klantcontact(
        client,
        onderwerp=subject,
        inhoud="Excuses voor de wachttijd, we hebben dit inmiddels doorgezet.",
    )
    add_inwoner_betrokkene(
        client, klantcontact_uuid=answer["uuid"], partij_uuid=partij_uuid
    )
    link_reply(client, klantcontact_uuid=answer["uuid"], parent_uuid=question["uuid"])
    return subject


def seed_multi_reply_thread(
    client: OpenKlantClient, *, partij_uuid: str, actor_uuid: str, tag: str
) -> str:
    """A question followed by several visible replies, each answering the previous."""
    subject = f"Vragen over mijn paspoortaanvraag [{tag}]"
    question = create_klantcontact(
        client, onderwerp=subject, inhoud="Wanneer kan ik mijn nieuwe paspoort ophalen?"
    )
    add_inwoner_betrokkene(
        client, klantcontact_uuid=question["uuid"], partij_uuid=partij_uuid
    )
    add_interne_taak(
        client,
        klantcontact_uuid=question["uuid"],
        actor_uuid=actor_uuid,
        status="verwerkt",
    )

    parent_uuid = question["uuid"]
    for inhoud in (
        "Uw paspoort ligt over 5 werkdagen klaar bij de balie.",
        "Kan iemand anders het voor mij ophalen met een machtiging?",
        "Ja, met een schriftelijke machtiging en een kopie van uw ID-bewijs.",
    ):
        reply = create_klantcontact(client, onderwerp=subject, inhoud=inhoud)
        add_inwoner_betrokkene(
            client, klantcontact_uuid=reply["uuid"], partij_uuid=partij_uuid
        )
        link_reply(client, klantcontact_uuid=reply["uuid"], parent_uuid=parent_uuid)
        parent_uuid = reply["uuid"]

    return subject


def seed_hidden_reply(
    client: OpenKlantClient, *, partij_uuid: str, actor_uuid: str, tag: str
) -> str:
    """A reply directly under the question, registered without the inwoner as betrokkene.

    The question is already in the listing, and asking what replies to it is the
    only way to find this one.
    """
    subject = f"Bezwaar tegen de parkeerboete [{tag}]"
    question = create_klantcontact(
        client,
        onderwerp=subject,
        inhoud="Ik wil bezwaar maken tegen deze parkeerboete.",
    )
    add_inwoner_betrokkene(
        client, klantcontact_uuid=question["uuid"], partij_uuid=partij_uuid
    )
    add_interne_taak(
        client,
        klantcontact_uuid=question["uuid"],
        actor_uuid=actor_uuid,
        status="verwerkt",
    )

    reply = create_klantcontact(
        client,
        onderwerp=subject,
        inhoud="We hebben uw bezwaar ontvangen en in behandeling genomen.",
    )
    add_staff_betrokkene(client, klantcontact_uuid=reply["uuid"])
    link_reply(client, klantcontact_uuid=reply["uuid"], parent_uuid=question["uuid"])
    return subject


def seed_hidden_mid_chain(
    client: OpenKlantClient, *, partij_uuid: str, actor_uuid: str, tag: str
) -> str:
    """A visible reply whose own parent is hidden.

    The reply is in the listing, but the klantcontact it replies to isn't, so
    fetching it by uuid is the only way in.
    """
    subject = f"Melding kapotte lantaarnpaal [{tag}]"
    question = create_klantcontact(
        client,
        onderwerp=subject,
        inhoud="De lantaarnpaal bij nummer 12 doet het al een week niet.",
    )
    add_inwoner_betrokkene(
        client, klantcontact_uuid=question["uuid"], partij_uuid=partij_uuid
    )
    add_interne_taak(
        client,
        klantcontact_uuid=question["uuid"],
        actor_uuid=actor_uuid,
        status="verwerkt",
    )

    hidden = create_klantcontact(
        client, onderwerp=subject, inhoud="Doorgezet naar de aannemer."
    )
    add_staff_betrokkene(client, klantcontact_uuid=hidden["uuid"])
    link_reply(client, klantcontact_uuid=hidden["uuid"], parent_uuid=question["uuid"])

    visible = create_klantcontact(
        client,
        onderwerp=subject,
        inhoud="De aannemer heeft de lantaarnpaal inmiddels gerepareerd.",
    )
    add_inwoner_betrokkene(
        client, klantcontact_uuid=visible["uuid"], partij_uuid=partij_uuid
    )
    link_reply(client, klantcontact_uuid=visible["uuid"], parent_uuid=hidden["uuid"])
    return subject


def seed_deep_hidden_chain(
    client: OpenKlantClient, *, partij_uuid: str, actor_uuid: str, tag: str
) -> str:
    """Two hidden replies in a row before a visible one.

    Looking up the visible reply's parent uncovers another missing parent in turn,
    so completing the chain takes two lookups instead of one.
    """
    subject = f"Vraag over de WOZ-beschikking [{tag}]"
    question = create_klantcontact(
        client,
        onderwerp=subject,
        inhoud="Ik snap de WOZ-waarde op mijn beschikking niet, kunt u dit toelichten?",
    )
    add_inwoner_betrokkene(
        client, klantcontact_uuid=question["uuid"], partij_uuid=partij_uuid
    )
    add_interne_taak(
        client,
        klantcontact_uuid=question["uuid"],
        actor_uuid=actor_uuid,
        status="verwerkt",
    )

    hidden_a = create_klantcontact(
        client, onderwerp=subject, inhoud="Doorgezet naar de afdeling belastingen."
    )
    add_staff_betrokkene(client, klantcontact_uuid=hidden_a["uuid"])
    link_reply(client, klantcontact_uuid=hidden_a["uuid"], parent_uuid=question["uuid"])

    hidden_b = create_klantcontact(
        client, onderwerp=subject, inhoud="Taxateur heeft het dossier opgevraagd."
    )
    add_staff_betrokkene(client, klantcontact_uuid=hidden_b["uuid"])
    link_reply(client, klantcontact_uuid=hidden_b["uuid"], parent_uuid=hidden_a["uuid"])

    visible = create_klantcontact(
        client,
        onderwerp=subject,
        inhoud="De WOZ-waarde is gebaseerd op de verkoopprijzen van vergelijkbare woningen.",
    )
    add_inwoner_betrokkene(
        client, klantcontact_uuid=visible["uuid"], partij_uuid=partij_uuid
    )
    link_reply(client, klantcontact_uuid=visible["uuid"], parent_uuid=hidden_b["uuid"])
    return subject


def seed_question_for_zaak(
    client: OpenKlantClient,
    *,
    partij_uuid: str,
    actor_uuid: str,
    tag: str,
    zaak_uuid: str,
) -> str:
    """A question tied to a real zaak, with one visible reply."""
    subject = f"Vraag over mijn lopende zaak [{tag}]"
    question = create_klantcontact(
        client,
        onderwerp=subject,
        inhoud="Kunt u mij vertellen wat de status is van mijn zaak?",
    )
    add_inwoner_betrokkene(
        client, klantcontact_uuid=question["uuid"], partij_uuid=partij_uuid
    )
    add_interne_taak(
        client,
        klantcontact_uuid=question["uuid"],
        actor_uuid=actor_uuid,
        status="te_verwerken",
    )
    link_zaak(client, klantcontact_uuid=question["uuid"], zaak_uuid=zaak_uuid)
    return subject


Scenario = Callable[..., str]

SCENARIOS: list[tuple[str, Scenario]] = [
    ("open question, no reply yet", seed_open_question),
    ("answered question (afgehandeld)", seed_answered_question),
    ("multi-reply thread, all visible", seed_multi_reply_thread),
    ("hidden reply directly under the question", seed_hidden_reply),
    ("visible reply, hidden parent", seed_hidden_mid_chain),
    ("visible reply, two hidden parents in a row", seed_deep_hidden_chain),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--token", default=DEFAULT_TOKEN)
    parser.add_argument("--bsn", default=DEFAULT_BSN)
    parser.add_argument("--first-name", default="Merel")
    parser.add_argument("--last-name", default="de Vries")
    parser.add_argument(
        "--zaak-uuid",
        default=None,
        help=(
            "uuid of a real zaak (e.g. from a local Open Zaak) to also seed a "
            "question tied to a zaak. Skipped if not given."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    client = OpenKlantClient(base_url=args.base_url, token=args.token)

    partij_uuid = get_or_create_partij(
        client, bsn=args.bsn, voornaam=args.first_name, achternaam=args.last_name
    )
    actor_uuid = get_or_create_actor(client, naam=ACTOR_NAAM)
    tag = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    scenarios = list(SCENARIOS)
    if args.zaak_uuid:
        scenarios.append(
            (
                "question tied to a zaak",
                lambda client, **kwargs: seed_question_for_zaak(
                    client, zaak_uuid=args.zaak_uuid, **kwargs
                ),
            )
        )

    print(f"Seeding conversations for BSN {args.bsn} against {args.base_url}\n")
    for description, seed in scenarios:
        subject = seed(client, partij_uuid=partij_uuid, actor_uuid=actor_uuid, tag=tag)
        print(f" - {subject}\n     {description}")

    print(
        f"\nDone. Log in locally with the DigiD mock for BSN {args.bsn} and open "
        "'Mijn vragen' to see them."
    )


if __name__ == "__main__":
    main()
