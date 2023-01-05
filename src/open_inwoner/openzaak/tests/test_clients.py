from django.core.cache import cache
from django.test import TestCase

from open_inwoner.openzaak.cases import (
    fetch_case_information_objects,
    fetch_case_information_objects_for_case_and_info,
    fetch_case_roles,
    fetch_cases,
    fetch_roles_for_case_and_bsn,
    fetch_single_case,
    fetch_single_result,
    fetch_specific_status,
    fetch_status_history,
)
from open_inwoner.openzaak.catalog import (
    fetch_single_case_type,
    fetch_single_status_type,
    fetch_status_types,
)
from open_inwoner.openzaak.clients import ZGWClients
from open_inwoner.openzaak.documents import (
    download_document,
    fetch_single_information_object_url,
    fetch_single_information_object_uuid,
)


class TestClients(TestCase):
    def setUp(self):
        super().setUp()
        cache.clear()

    def tearDown(self):
        super().tearDown()
        cache.clear()

    def test_clients_without_config_dont_crash(self):
        with self.subTest("not used"):
            clients = ZGWClients()
            clients.close()

        with self.subTest("after clients lazy-init property access"):
            clients = ZGWClients()
            tmp = clients.zaak
            tmp = clients.catalogi
            tmp = clients.document
            clients.close()

    def test_methods_without_config_dont_crash_but_return_empty(self):
        clients = ZGWClients()
        with self.subTest("zaak api"):
            self.assertEqual([], fetch_cases(clients.zaak, "12345678"))
            self.assertIsNone(fetch_single_case(clients.zaak, "my_uuid"))
            self.assertEqual([], fetch_case_information_objects(clients.zaak, "my_url"))
            self.assertEqual([], fetch_status_history(clients.zaak, "my_url"))
            self.assertIsNone(fetch_specific_status(clients.zaak, "my_url"))
            self.assertEqual([], fetch_case_roles(clients.zaak, "my_url"))
            self.assertEqual(
                [], fetch_roles_for_case_and_bsn(clients.zaak, "my_url", "12345678")
            )
            self.assertEqual(
                [],
                fetch_case_information_objects_for_case_and_info(
                    clients.zaak, "my_url", "my_url"
                ),
            )
            self.assertIsNone(fetch_single_result(clients.zaak, "my_url"))

        with self.subTest("catalogi api"):
            self.assertEqual([], fetch_status_types(clients.catalogi, "my_url"))
            self.assertIsNone(fetch_single_status_type(clients.catalogi, "my_url"))
            self.assertIsNone(fetch_single_case_type(clients.catalogi, "my_url"))

        with self.subTest("document api"):
            self.assertIsNone(
                fetch_single_information_object_url(clients.document, "my_url")
            )
            self.assertIsNone(
                fetch_single_information_object_uuid(clients.document, "my_uuid")
            )
            self.assertIsNone(download_document(clients.document, "my_uuid"))
