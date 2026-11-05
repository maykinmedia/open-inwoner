import datetime as dt
from unittest.mock import Mock

from django.test import TestCase

import requests_mock

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.gesprekken.client import build_gesprekken_client, uuid_from_url
from open_inwoner.gesprekken.forms import GesprekStartForm
from open_inwoner.gesprekken.models import GesprekGezien, MijnGesprekkenConfig
from open_inwoner.gesprekken.services import (
    afzender_naam,
    build_gesprek_view,
    eigen_deelname,
    mark_seen,
)
from open_inwoner.openzaak.tests.factories import ServiceFactory

from .shared import (
    GESPREKKEN_ROOT,
    PARTIJ_DEELNAME,
    PARTIJ_UUID,
    ZAAK_URL,
    gesprek_detail,
)


class ReferenceTests(TestCase):
    def test_uuid_from_url(self):
        self.assertEqual(
            uuid_from_url(f"{GESPREKKEN_ROOT}gesprekken/abc/"),
            "abc",
        )
        self.assertIsNone(uuid_from_url(None))

    def test_eigen_deelname_is_the_url_of_the_deelname_of_the_partij(self):
        gesprek = gesprek_detail()

        self.assertEqual(eigen_deelname(gesprek, PARTIJ_UUID), PARTIJ_DEELNAME)
        self.assertIsNone(
            eigen_deelname(gesprek, "dddddddd-dddd-dddd-dddd-dddddddddddd")
        )
        # Without a Klanten API: the only active partij-deelname
        self.assertEqual(eigen_deelname(gesprek, None), PARTIJ_DEELNAME)

    def test_own_bijdragen_are_recognised_by_the_verzender_url(self):
        view = build_gesprek_view(
            gesprek_detail(), PARTIJ_UUID, MijnGesprekkenConfig.get_solo()
        )

        self.assertEqual(view.eigen_deelname, PARTIJ_DEELNAME)
        self.assertEqual([b.is_eigen for b in view.bijdragen], [True, False])


@requests_mock.Mocker()
class CursorPaginationTests(TestCase):
    def setUp(self):
        config = MijnGesprekkenConfig.get_solo()
        config.service = ServiceFactory(api_root=GESPREKKEN_ROOT)
        config.save()

    def test_list_for_zaak_follows_the_next_link_until_it_is_null(self, m):
        tweede = f"{GESPREKKEN_ROOT}gesprekken?aanleidingZaak={ZAAK_URL}&cursor=abc"
        m.get(
            f"{GESPREKKEN_ROOT}gesprekken?aanleidingZaak={ZAAK_URL}",
            [
                {"json": {"next": tweede, "count": 2, "results": [{"uuid": "1"}]}},
            ],
            complete_qs=True,
        )
        m.get(
            tweede,
            json={"next": None, "count": 2, "results": [{"uuid": "2"}]},
            complete_qs=True,
        )

        gesprekken = build_gesprekken_client().list_for_zaak(ZAAK_URL)

        self.assertEqual([g["uuid"] for g in gesprekken], ["1", "2"])
        # The second request is the next link as given, with the filter in it
        self.assertIn("cursor=abc", m.request_history[1].url)
        self.assertIn("aanleidingZaak=", m.request_history[1].url)


class GesprekStartFormTests(TestCase):
    def test_onderwerp_fits_the_gesprekken_api(self):
        data = {"tekst": "Vraag", "onderwerp": "a" * 200}

        self.assertTrue(GesprekStartForm(data).is_valid())
        self.assertFalse(GesprekStartForm({**data, "onderwerp": "a" * 201}).is_valid())


class AutomatischEnNamensTests(TestCase):
    def test_an_automatic_reply_is_recognisable(self):
        detail = gesprek_detail()
        detail["gespreksbijdragen"][1]["automatisch"] = True

        view = build_gesprek_view(detail, PARTIJ_UUID, MijnGesprekkenConfig.get_solo())

        self.assertFalse(view.bijdragen[0].automatisch)
        self.assertTrue(view.bijdragen[1].automatisch)
        self.assertEqual(view.bijdragen[1].afzender, "Automatisch bericht")

    def test_a_representative_is_shown_with_the_partij_it_acts_for(self):
        deelnames = {
            "a": {"naam": "C. Curator", "namens": "https://kic/partijen/1"},
            "b": {"naam": "Sanne", "partij": "https://kic/partijen/1"},
        }

        self.assertEqual(
            afzender_naam(deelnames["a"], deelnames), "C. Curator, namens Sanne"
        )
        self.assertEqual(afzender_naam(deelnames["b"], deelnames), "Sanne")


class MarkSeenTests(TestCase):
    def test_a_bijdrage_of_just_before_the_previous_render_is_still_registered(self):
        """Leveringsmoment has seconds only; a render in the same second must not hide it."""
        user = UserFactory()
        gesprek = gesprek_detail()
        client = Mock()
        view = build_gesprek_view(gesprek, PARTIJ_UUID, MijnGesprekkenConfig.get_solo())
        moment = view.bijdragen[1].moment
        GesprekGezien.objects.create(
            user=user,
            gesprek_url=gesprek["url"],
            gezien_op=moment + dt.timedelta(milliseconds=400),
        )

        mark_seen(client, user, gesprek, view)

        client.mark_gelezen.assert_called_once_with(
            view.bijdragen[1].uuid, PARTIJ_DEELNAME
        )

    def test_old_bijdragen_are_not_registered_again(self):
        user = UserFactory()
        gesprek = gesprek_detail()
        client = Mock()
        view = build_gesprek_view(gesprek, PARTIJ_UUID, MijnGesprekkenConfig.get_solo())
        GesprekGezien.objects.create(
            user=user,
            gesprek_url=gesprek["url"],
            gezien_op=view.bijdragen[1].moment + dt.timedelta(hours=1),
        )

        mark_seen(client, user, gesprek, view)

        client.mark_gelezen.assert_not_called()
