from django.test import TestCase

from open_inwoner.mijn_afval.clients import AfvalApiClient
from open_inwoner.mijn_afval.constants import AfvalType


class AfvalClientTest(TestCase):
    def test_client_fetch_bag_objects_success(self):
        client = AfvalApiClient(base_url="")

        data = client.fetch_bag_objects_for_bsn(bsn="42")

        first = data[0]
        self.assertEqual(first.object_address, "Kerkstraat 12")
        self.assertEqual(first.totaal_gewicht, 1245)

        containers = first.containers
        self.assertEqual(containers[0].type, AfvalType.RESTAFVAL)
        self.assertEqual(containers[0].totaal_gewicht, 720)
        self.assertEqual(containers[1].type, AfvalType.GFT)
        self.assertEqual(containers[1].totaal_gewicht, 385)

        ledigingen = first.containers[0].ledigingen
        self.assertEqual(len(ledigingen), 15)

        second = data[1]
        self.assertEqual(second.object_address, "Hoofdweg 45A")
        self.assertEqual(second.totaal_gewicht, 1680)

        containers = second.containers
        self.assertEqual(containers[0].type, AfvalType.RESTAFVAL)
        self.assertEqual(containers[0].totaal_gewicht, 1120)

        ledigingen = second.containers[0].ledigingen
        self.assertEqual(len(ledigingen), 14)
