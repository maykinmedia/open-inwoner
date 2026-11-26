import json
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

import requests_mock

from open_inwoner.gesprekken.events import parse_sse
from open_inwoner.gesprekken.models import (
    GesprekkenEventStroom,
    MijnGesprekkenConfig,
    VerwerktGesprekEvent,
)
from open_inwoner.gesprekken.services import get_versie
from open_inwoner.openzaak.tests.factories import ServiceFactory
from open_inwoner.utils.test import ClearCachesMixin

from .shared import (
    ACTOR_DEELNAME,
    GESPREK_URL,
    GESPREK_UUID,
    GESPREKKEN_ROOT,
    PARTIJ_DEELNAME,
    ZAAK_URL,
    gesprek_detail,
)

EVENTS_URL = f"{GESPREKKEN_ROOT}events"


def cloud_event(sequence: int, type_: str, data: dict) -> str:
    event = {
        "specversion": "1.0",
        "id": f"event-{sequence}",
        "source": GESPREKKEN_ROOT,
        "type": type_,
        "subject": GESPREK_URL,
        "time": "2026-07-13T07:30:00.000Z",
        "sequence": str(sequence),
        "datacontenttype": "application/json",
        "aanleidingzaak": ZAAK_URL,
        "data": data,
    }
    return f"id: {sequence}\nevent: {type_}\ndata: {json.dumps(event)}\n\n"


def bijdrage_event(sequence: int, verzender: str) -> str:
    return cloud_event(
        sequence,
        "nl.vng.gesprekken.gespreksbijdrage.aangemaakt",
        {"uuid": f"b{sequence}", "gesprek": GESPREK_URL, "verzender": verzender},
    )


class ParseSseTests(TestCase):
    def test_events_comments_and_multiline_data(self):
        lines = [
            ": ping",
            "",
            "id: 7",
            "event: x",
            'data: {"a":',
            "data: 1}",
            "",
            "id: 8",
            "data: {}",
            "",
        ]

        events = list(parse_sse(lines))

        self.assertEqual([(e.id, e.event) for e in events], [("7", "x"), ("8", None)])
        self.assertEqual(json.loads(events[0].data), {"a": 1})


@requests_mock.Mocker()
@patch("open_inwoner.gesprekken.tasks.send_gesprek_bijdrage_email.apply_async")
class VolgGesprekkenEventsTests(ClearCachesMixin, TestCase):
    def setUp(self):
        super().setUp()
        config = MijnGesprekkenConfig.get_solo()
        config.enabled = True
        config.service = ServiceFactory(api_root=GESPREKKEN_ROOT)
        config.email_vertraging_minuten = 10
        config.save()

    def run_command(self):
        call_command(
            "volg_gesprekken_events", "--once", stdout=StringIO(), stderr=StringIO()
        )

    def test_an_automatic_reply_does_not_plan_an_email(self, m, mock_email):
        m.get(f"{GESPREKKEN_ROOT}gesprekken/{GESPREK_UUID}", json=gesprek_detail())
        m.get(
            EVENTS_URL,
            text=cloud_event(
                42,
                "nl.vng.gesprekken.gespreksbijdrage.aangemaakt",
                {
                    "uuid": "b42",
                    "gesprek": GESPREK_URL,
                    "verzender": ACTOR_DEELNAME,
                    "automatisch": True,
                },
            ),
        )

        self.run_command()

        mock_email.assert_not_called()

    def test_events_are_processed_and_the_cursor_is_stored(self, m, mock_email):
        m.get(f"{GESPREKKEN_ROOT}gesprekken/{GESPREK_UUID}", json=gesprek_detail())
        m.get(
            EVENTS_URL,
            text=": ping\n\n"
            + cloud_event(
                41, "nl.vng.gesprekken.gesprek.aangemaakt", {"uuid": GESPREK_UUID}
            )
            + bijdrage_event(42, ACTOR_DEELNAME)
            + bijdrage_event(43, PARTIJ_DEELNAME),
            headers={"Content-Type": "text/event-stream"},
        )

        self.run_command()

        self.assertEqual(GesprekkenEventStroom.get_solo().cursor, "43")
        self.assertNotEqual(get_versie(ZAAK_URL), "0")
        self.assertEqual(VerwerktGesprekEvent.objects.count(), 3)
        # Only the bijdrage of the municipality plans an e-mail
        mock_email.assert_called_once()
        self.assertEqual(
            mock_email.call_args.kwargs["args"][:2], [GESPREK_URL, ZAAK_URL]
        )
        self.assertEqual(mock_email.call_args.kwargs["countdown"], 600)

    def test_the_stream_resumes_from_the_stored_cursor(self, m, mock_email):
        GesprekkenEventStroom.objects.update_or_create(defaults={"cursor": "41"})
        m.get(EVENTS_URL, text="", headers={"Content-Type": "text/event-stream"})

        self.run_command()

        self.assertEqual(m.last_request.headers["Last-Event-ID"], "41")

    def test_without_a_cursor_no_last_event_id_is_sent(self, m, mock_email):
        m.get(EVENTS_URL, text="", headers={"Content-Type": "text/event-stream"})

        self.run_command()

        self.assertNotIn("Last-Event-ID", m.last_request.headers)

    def test_an_event_seen_before_is_not_processed_again(self, m, mock_email):
        VerwerktGesprekEvent.objects.create(event_id="event-42")
        m.get(f"{GESPREKKEN_ROOT}gesprekken/{GESPREK_UUID}", json=gesprek_detail())
        m.get(
            EVENTS_URL,
            text=bijdrage_event(42, ACTOR_DEELNAME),
            headers={"Content-Type": "text/event-stream"},
        )

        self.run_command()

        mock_email.assert_not_called()
        self.assertEqual(GesprekkenEventStroom.get_solo().cursor, "42")

    def test_an_event_without_aanleidingzaak_is_skipped_and_the_cursor_moves_on(
        self, m, mock_email
    ):
        event = bijdrage_event(44, ACTOR_DEELNAME).replace(
            f', "aanleidingzaak": "{ZAAK_URL}"', ""
        )
        self.assertNotIn("aanleidingzaak", event)
        m.get(EVENTS_URL, text=event, headers={"Content-Type": "text/event-stream"})

        self.run_command()

        mock_email.assert_not_called()
        self.assertEqual(get_versie(ZAAK_URL), "0")
        self.assertEqual(GesprekkenEventStroom.get_solo().cursor, "44")

    def test_a_malformed_event_is_skipped_and_the_next_one_is_processed(
        self, m, mock_email
    ):
        m.get(f"{GESPREKKEN_ROOT}gesprekken/{GESPREK_UUID}", json=gesprek_detail())
        zonder_subject = bijdrage_event(46, ACTOR_DEELNAME).replace(
            f'"subject": "{GESPREK_URL}", ', ""
        )
        self.assertNotIn('"subject"', zonder_subject)
        m.get(
            EVENTS_URL,
            text="id: 45\ndata: {geen json\n\n"
            + zonder_subject
            + bijdrage_event(47, ACTOR_DEELNAME).replace(
                '"2026-07-13T07:30:00.000Z"', '"gisteren"'
            )
            + bijdrage_event(48, ACTOR_DEELNAME),
            headers={"Content-Type": "text/event-stream"},
        )

        self.run_command()

        self.assertEqual(GesprekkenEventStroom.get_solo().cursor, "48")
        self.assertEqual(
            list(VerwerktGesprekEvent.objects.values_list("event_id", flat=True)),
            ["event-48"],
        )
        mock_email.assert_called_once()

    def test_an_expired_cursor_continues_from_a_new_snapshot(self, m, mock_email):
        GesprekkenEventStroom.objects.update_or_create(defaults={"cursor": "3"})
        m.get(
            EVENTS_URL,
            [
                {"status_code": 410, "json": {"code": "cursor-verlopen"}},
                {
                    "text": cloud_event(
                        51,
                        "nl.vng.gesprekken.gesprek.beeindigd",
                        {"uuid": GESPREK_UUID},
                    ),
                    "headers": {"Content-Type": "text/event-stream"},
                },
            ],
        )
        m.get(
            f"{GESPREKKEN_ROOT}gesprekken?pageSize=1",
            json={"count": 0, "next": None, "previous": None, "results": []},
            headers={"Feed-Cursor": "50"},
        )

        self.run_command()

        stream_requests = [r for r in m.request_history if r.path.endswith("/events")]
        self.assertEqual(
            [r.headers.get("Last-Event-ID") for r in stream_requests], ["3", "50"]
        )
        self.assertEqual(GesprekkenEventStroom.get_solo().cursor, "51")

    def test_nothing_happens_when_disabled(self, m, mock_email):
        MijnGesprekkenConfig.objects.update(enabled=False)

        self.run_command()

        self.assertEqual(m.call_count, 0)
