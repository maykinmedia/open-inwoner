"""
Following the event stream (GET /events) of the Gesprekken API, with the
`volg_gesprekken_events` command. Events carry references only. The portal uses a
change to
- mark the gesprekken of the zaak as changed, so an open page refreshes;
- plan an e-mail to the resident after a new bijdrage of the municipality,
  sent only if the resident has not seen it by then.
"""

import datetime as dt
import json
from collections.abc import Iterable, Iterator
from dataclasses import dataclass

from django.db import IntegrityError, transaction
from django.utils.dateparse import parse_datetime

import structlog

from .client import GesprekkenAPIError, GesprekkenClient, uuid_from_url
from .models import GesprekkenEventStroom, MijnGesprekkenConfig, VerwerktGesprekEvent
from .services import bump_versie
from .tasks import send_gesprek_bijdrage_email

logger = structlog.stdlib.get_logger(__name__)

EVENT_BIJDRAGE_AANGEMAAKT = "nl.vng.gesprekken.gespreksbijdrage.aangemaakt"


@dataclass
class SseEvent:
    id: str | None
    event: str | None
    data: str


def parse_sse(lines: Iterable[str]) -> Iterator[SseEvent]:
    """Parses a Server-Sent Events stream; comment lines (pings) are skipped."""
    event_id, event, data = None, None, []
    for line in lines:
        if line == "":
            if data:
                yield SseEvent(event_id, event, "\n".join(data))
            event_id, event, data = None, None, []
        elif line.startswith(":"):
            continue
        else:
            field, _, value = line.partition(":")
            value = value.removeprefix(" ")
            if field == "id":
                event_id = value
            elif field == "event":
                event = value
            elif field == "data":
                data.append(value)


class VerzenderTypes:
    """Looks up whether a deelname is an actor or a partij, one gesprek at a time."""

    def __init__(self, client: GesprekkenClient):
        self.client = client
        self.cache: dict[str, str] = {}

    def __call__(self, gesprek_url: str | None, deelname_url: str | None) -> str | None:
        if not gesprek_url or not deelname_url:
            return None
        if deelname_url not in self.cache:
            try:
                gesprek = self.client.get_gesprek(uuid_from_url(gesprek_url))
            except GesprekkenAPIError:
                logger.exception("Could not look up verzender", gesprek=gesprek_url)
                return None
            for deelname in gesprek.get("gespreksdeelnames", []):
                self.cache[deelname["url"]] = deelname.get("type")
        return self.cache.get(deelname_url)


def verwerk_wijziging(
    *,
    event_id: str | None,
    zaak_url: str,
    gesprek_url: str,
    nieuwe_bijdrage_van_gemeente: bool,
    moment: dt.datetime,
) -> str:
    """Process one change; a change seen before (by its id) is ignored."""
    if event_id:
        try:
            with transaction.atomic():
                VerwerktGesprekEvent.objects.create(event_id=event_id)
        except IntegrityError:
            return f"ignored: event {event_id} was already processed"

    bump_versie(zaak_url)

    if nieuwe_bijdrage_van_gemeente:
        config = MijnGesprekkenConfig.get_solo()
        send_gesprek_bijdrage_email.apply_async(
            args=[gesprek_url, zaak_url, moment.isoformat()],
            countdown=dt.timedelta(
                minutes=config.email_vertraging_minuten
            ).total_seconds(),
        )
        return "processed: page marked as changed, e-mail planned"

    return "processed: page marked as changed"


def handle_cloud_event(cloud_event: dict, verzender_type) -> str:
    """
    Process a CloudEvent from the event stream. `verzender_type(gesprek_url,
    deelname_url)` tells whether a bijdrage came from an actor or a partij; it is
    only called for new bijdragen.
    """
    zaak_url = cloud_event.get("aanleidingzaak")
    if not zaak_url:
        return "ignored: event has no aanleidingzaak"

    data = cloud_event.get("data") or {}
    nieuwe_bijdrage_van_gemeente = (
        cloud_event.get("type") == EVENT_BIJDRAGE_AANGEMAAKT
        and not data.get("automatisch")
        and verzender_type(data.get("gesprek"), data.get("verzender")) == "actor"
    )
    return verwerk_wijziging(
        event_id=cloud_event.get("id"),
        zaak_url=zaak_url,
        gesprek_url=cloud_event["subject"],
        nieuwe_bijdrage_van_gemeente=nieuwe_bijdrage_van_gemeente,
        moment=parse_datetime(cloud_event["time"]),
    )


def follow(client: GesprekkenClient, *, timeout: float = 60) -> int:
    """
    Reads the stream from the stored cursor until the connection ends, processing
    and storing the cursor event by event. Returns the number of events processed.

    A cursor the API no longer has (410) is replaced, as patterns/event-stream
    prescribes, by the Feed-Cursor of a new snapshot, and the stream is opened
    again from there. The portal keeps no copy of the gesprekken (pages fetch
    their own snapshot), so only e-mails for changes in between are lost.
    """
    stroom = GesprekkenEventStroom.get_solo()
    try:
        response = client.open_event_stream(stroom.cursor or None, timeout=timeout)
    except GesprekkenAPIError as exc:
        if exc.status_code != 410:
            raise
        verlopen = stroom.cursor
        stroom.cursor = client.feed_cursor()
        stroom.save(update_fields=["cursor", "bijgewerkt_op"])
        logger.warning(
            "Event stream cursor expired; continuing from a new snapshot",
            verlopen=verlopen,
            cursor=stroom.cursor,
        )
        response = client.open_event_stream(stroom.cursor, timeout=timeout)

    verzender_types = VerzenderTypes(client)
    processed = 0
    with response:
        for sse in parse_sse(response.iter_lines(decode_unicode=True)):
            outcome = handle_cloud_event(json.loads(sse.data), verzender_types)
            logger.info("Processed gesprekken event", id=sse.id, outcome=outcome)
            if sse.id:
                stroom.cursor = sse.id
                stroom.save(update_fields=["cursor", "bijgewerkt_op"])
            processed += 1
    return processed
