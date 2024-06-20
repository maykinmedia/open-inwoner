from unittest import TestCase as PlainTestCase

from django.test import TestCase

import requests
import requests_mock
from zgw_consumers.constants import APITypes

from open_inwoner.openzaak.clients import (
    MultiZgwClientProxy,
    MultiZgwClientProxyResult,
    ZgwClientResponse,
    build_catalogi_client,
    build_catalogi_clients,
    build_documenten_client,
    build_documenten_clients,
    build_forms_client,
    build_forms_clients,
    build_zaken_client,
    build_zaken_clients,
)
from open_inwoner.openzaak.exceptions import MultiZgwClientProxyError
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
            client = factory()
            self.assertEqual(
                client.configured_from, getattr(self.api_groups[0], api_group_field)
            )
            self.assertEqual(client.configured_from.api_type, api_type)

    def test_originating_service_is_persisted_on_all_clients(self):
        for factory, api_type, api_group_field in (
            (build_forms_clients, APITypes.orc, "form_service"),
            (build_zaken_clients, APITypes.zrc, "zrc_service"),
            (build_documenten_clients, APITypes.drc, "drc_service"),
            (build_catalogi_clients, APITypes.ztc, "ztc_service"),
        ):
            clients = factory()
            for i, client in enumerate(clients):
                self.assertEqual(
                    client.configured_from, getattr(self.api_groups[i], api_group_field)
                )
                self.assertEqual(client.configured_from.api_type, api_type)


class SimpleClient:
    def __init__(self, url):
        self.url = url

    def fetch_rows(self):
        resp = requests.get(self.url)
        return resp.json()


@requests_mock.Mocker()
class MultiZgwClientProxyTests(PlainTestCase):
    def setUp(self):
        self.a_url = "http://foo/bar/rows"
        self.another_url = "http://bar/baz/rows"

        self.a_client = SimpleClient(self.a_url)
        self.another_client = SimpleClient(self.another_url)

    def test_all_successful_responses_are_returned(self, m):
        m.get(self.a_url, json=["foo", "bar"])
        m.get(self.another_url, json=["bar", "baz"])
        proxy = MultiZgwClientProxy([self.a_client, self.another_client])

        result = proxy.fetch_rows()
        expected = MultiZgwClientProxyResult(
            # Note this list is deterministic because, under the hood, requests_mock
            # handles requests sequentially rather than in parallel. Normally, the
            # order would depend on the thread completion order.
            responses=[
                ZgwClientResponse(
                    client=self.a_client, result=["foo", "bar"], exception=None
                ),
                ZgwClientResponse(
                    client=self.another_client, result=["bar", "baz"], exception=None
                ),
            ]
        )
        self.assertEqual(
            result.responses,
            [
                ZgwClientResponse(
                    client=self.a_client, result=["foo", "bar"], exception=None
                ),
                ZgwClientResponse(
                    client=self.another_client, result=["bar", "baz"], exception=None
                ),
            ],
        )
        self.assertEqual(result.responses, result.successful_responses)
        self.assertEqual(result.failing_responses, [])
        self.assertEqual(result.join_results(), ["foo", "bar", "bar", "baz"])
        self.assertEqual(
            result.raise_on_failures(),
            None,
            msg="raise_on_failures is a noop if all responses are successful",
        )

    def test_partial_exceptions_are_returned(self, m):
        m.get(self.a_url, json=["foo", "bar"])
        m.get(self.another_url, exc=requests.exceptions.Timeout)

        proxy = MultiZgwClientProxy([self.a_client, self.another_client])

        result = proxy.fetch_rows()
        successful_response, failing_response = result.responses
        self.assertEqual(
            successful_response,
            ZgwClientResponse(
                client=self.a_client, result=["foo", "bar"], exception=None
            ),
        )
        self.assertEqual(
            result.join_results(),
            ["foo", "bar"],
            msg="Only successful results should be joined",
        )

        # It's non-trivial to compare exceptions on equality, so we have to split this up
        self.assertEqual(
            (failing_response.client, failing_response.result),
            (self.another_client, None),
        )
        self.assertIsInstance(failing_response.exception, requests.exceptions.Timeout)
        self.assertEqual(result.has_errors, True)

        with self.assertRaises(MultiZgwClientProxyError) as cm:
            result.raise_on_failures()

        self.assertTrue(
            [e.__class__ for e in cm.exception.exceptions],
            [requests.exceptions.Timeout],
        )
        self.assertEqual(len(result.failing_responses), 1)

    def test_result_can_be_used_as_response_iterator(self, m):
        m.get(self.a_url, json=["foo", "bar"])
        m.get(self.another_url, json=["bar", "baz"])
        proxy = MultiZgwClientProxy([self.a_client, self.another_client])

        result = proxy.fetch_rows()

        # Verify that each invocation yields a fresh generator with a clean iteration state
        for _ in range(2):
            self.assertEqual(
                [row.result for row in result], [["foo", "bar"], ["bar", "baz"]]
            )
