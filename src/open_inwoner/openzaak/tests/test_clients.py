from django.test import TestCase

from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service

from open_inwoner.openzaak.clients import (
    build_catalogi_client,
    build_documenten_client,
    build_forms_client,
    build_zaken_client,
)
from open_inwoner.openzaak.tests.factories import ZGWApiGroupConfigFactory


class ClientFactoryTestCase(TestCase):
    def setUp(self):
        ZGWApiGroupConfigFactory()

    def test_originating_service_is_persisted_on_client(self):
        for factory, api_type in (
            (build_forms_client, APITypes.orc),
            (build_zaken_client, APITypes.zrc),
            (build_documenten_client, APITypes.drc),
            (build_catalogi_client, APITypes.ztc),
        ):
            client = factory()
            self.assertIsInstance(client.configured_from, Service)
            self.assertEqual(client.configured_from.api_type, api_type)
