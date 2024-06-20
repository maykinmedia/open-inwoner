from django.test import TestCase

from zgw_consumers.constants import APITypes

from open_inwoner.openzaak.clients import (
    build_catalogi_client,
    build_catalogi_clients,
    build_documenten_client,
    build_documenten_clients,
    build_forms_client,
    build_forms_clients,
    build_zaken_client,
    build_zaken_clients,
)
from open_inwoner.openzaak.tests.factories import ZGWApiGroupConfigFactory


class ClientFactoryTestCase(TestCase):
    def setUp(self):
        self.api_groups = [
            ZGWApiGroupConfigFactory(name="Default API"),
            ZGWApiGroupConfigFactory(name="Second API"),
        ]

    def test_originating_service_is_persisted_on_client(self):
        for factory, api_type, api_group_field in (
            (build_forms_client, APITypes.orc, "form_service"),
            (build_zaken_client, APITypes.zrc, "zrc_service"),
            (build_documenten_client, APITypes.drc, "drc_service"),
            (build_catalogi_client, APITypes.ztc, "ztc_service"),
        ):
            with self.subTest(
                f"Client of type {api_type} persists originating service"
            ):
                client = factory()
                self.assertEqual(
                    client.configured_from,
                    getattr(self.api_groups[0], api_group_field),
                )
                self.assertEqual(client.configured_from.api_type, api_type)

    def test_originating_service_is_persisted_on_all_clients(self):
        for factory, api_type, api_group_field in (
            (build_forms_clients, APITypes.orc, "form_service"),
            (build_zaken_clients, APITypes.zrc, "zrc_service"),
            (build_documenten_clients, APITypes.drc, "drc_service"),
            (build_catalogi_clients, APITypes.ztc, "ztc_service"),
        ):
            with self.subTest(
                f"All clients of type {api_type} persist originating service"
            ):
                clients = factory()
                for i, client in enumerate(clients):
                    self.assertEqual(
                        client.configured_from,
                        getattr(self.api_groups[i], api_group_field),
                    )
                    self.assertEqual(client.configured_from.api_type, api_type)
