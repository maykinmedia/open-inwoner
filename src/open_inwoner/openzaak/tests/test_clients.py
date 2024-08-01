from unittest import TestCase as PlainTestCase
from unittest.mock import Mock, patch

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
    build_zgw_client_from_service,
)
from open_inwoner.openzaak.exceptions import MultiZgwClientProxyError
from open_inwoner.openzaak.models import ZGWApiGroupConfig
from open_inwoner.openzaak.tests.factories import ZGWApiGroupConfigFactory
from open_inwoner.openzaak.tests.shared import (
    CATALOGI_ROOT,
    DOCUMENTEN_ROOT,
    ZAKEN_ROOT,
)


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


class ZGWApiGroupConfigFilterTests(TestCase):
    def setUp(self):
        self.api_groups = [
            ZGWApiGroupConfigFactory(
                name="Default API",
                ztc_service__api_root=CATALOGI_ROOT,
                zrc_service__api_root=ZAKEN_ROOT,
                drc_service__api_root=DOCUMENTEN_ROOT,
                form_service__api_root="http://some.forms.nl",
            ),
            ZGWApiGroupConfigFactory(name="Second API"),
        ]

    def test_groups_can_be_filtered_by_client(self):
        for factory, api_type in (
            (build_forms_clients, APITypes.orc),
            (build_zaken_clients, APITypes.zrc),
            (build_documenten_clients, APITypes.drc),
            (build_catalogi_clients, APITypes.ztc),
        ):
            with self.subTest(
                f"ZGWApiGroupConfig can be filtered by clients of type {api_type}"
            ):
                clients = factory()
                for i, client in enumerate(clients):
                    value = list(ZGWApiGroupConfig.objects.filter_by_zgw_client(client))
                    expected = [self.api_groups[i]]
                    self.assertEqual(value, expected)

    def test_filtering_groups_by_client_with_non_client_type_raises(self):
        with self.assertRaises(ValueError):
            ZGWApiGroupConfig.objects.filter_by_zgw_client("Not a client")

    def test_filter_by_service(self):
        for api_type, api_group_field in (
            (APITypes.orc, "form_service"),
            (APITypes.zrc, "zrc_service"),
            (APITypes.drc, "drc_service"),
            (APITypes.ztc, "ztc_service"),
        ):
            with self.subTest(
                f"ZGWApiGroupConfig can be filtered by services of type {api_type}"
            ):
                service = getattr(self.api_groups[0], api_group_field)

                self.assertEqual(
                    list(ZGWApiGroupConfig.objects.filter_by_service(service)),
                    [self.api_groups[0]],
                )

    def test_filter_by_root_url_overlap(self):
        for root, api_group_field in (
            ("http://some.forms.nl", "form_service"),
            (ZAKEN_ROOT, "zrc_service"),
            (DOCUMENTEN_ROOT, "drc_service"),
            (ZAKEN_ROOT, "ztc_service"),
        ):
            with self.subTest(
                f"ZGWApiGroupConfig can be filtered by URL for {api_group_field}"
            ):
                self.assertEqual(
                    list(ZGWApiGroupConfig.objects.filter_by_url_root_overlap(root)),
                    [self.api_groups[0]],
                )

    def test_resolve_group_from_hints_raises_on_no_args(self):
        with self.assertRaises(ZGWApiGroupConfig.DoesNotExist):
            ZGWApiGroupConfig.objects.resolve_group_from_hints()

    @patch(
        "open_inwoner.openzaak.models.ZGWApiGroupConfigQuerySet.filter_by_zgw_client"
    )
    @patch(
        "open_inwoner.openzaak.models.ZGWApiGroupConfigQuerySet.filter_by_url_root_overlap"
    )
    def test_resolve_group_from_hints_uses_service_as_highest_priority(
        self, filter_by_zgw_client_mock, filter_by_url_root_overlap_mock
    ):
        for group in self.api_groups:
            for service_field in (
                "form_service",
                "zrc_service",
                "drc_service",
                "ztc_service",
            ):
                service = getattr(group, service_field)
                client = build_zgw_client_from_service(service)
                url = service.api_root
                self.assertEqual(
                    ZGWApiGroupConfig.objects.resolve_group_from_hints(
                        service=service, client=client, url=url
                    ),
                    group,
                )

        filter_by_zgw_client_mock.assert_not_called()
        filter_by_url_root_overlap_mock.assert_not_called()

    @patch("open_inwoner.openzaak.models.ZGWApiGroupConfigQuerySet.filter_by_service")
    @patch(
        "open_inwoner.openzaak.models.ZGWApiGroupConfigQuerySet.filter_by_url_root_overlap"
    )
    def test_resolve_group_from_hints_uses_client_as_middle_priority(
        self, filter_by_service_mock, filter_by_url_root_overlap_mock
    ):
        for factory in (
            build_forms_clients,
            build_zaken_clients,
            build_documenten_clients,
            build_catalogi_clients,
        ):
            clients = factory()
            for i, client in enumerate(clients):
                for service_field in (
                    "form_service",
                    "zrc_service",
                    "drc_service",
                    "ztc_service",
                ):
                    service = getattr(self.api_groups[i], service_field)
                    url = service.api_root
                    self.assertEqual(
                        ZGWApiGroupConfig.objects.resolve_group_from_hints(
                            client=client, url=url
                        ),
                        self.api_groups[i],
                    )

                    filter_by_service_mock.assert_not_called()
                    filter_by_url_root_overlap_mock.assert_not_called()

    @patch("open_inwoner.openzaak.models.ZGWApiGroupConfigQuerySet.filter_by_service")
    @patch(
        "open_inwoner.openzaak.models.ZGWApiGroupConfigQuerySet.filter_by_zgw_client"
    )
    def test_resolve_group_from_hints_uses_url_as_lowest_priority(
        self, filter_by_service_mock, filter_by_zgw_client_mock
    ):
        for group in self.api_groups:
            for service_field in (
                "form_service",
                "zrc_service",
                "drc_service",
                "ztc_service",
            ):
                service = getattr(group, service_field)

                self.assertEqual(
                    ZGWApiGroupConfig.objects.resolve_group_from_hints(
                        url=service.api_root
                    ),
                    group,
                )

                filter_by_service_mock.assert_not_called()
                filter_by_zgw_client_mock.assert_not_called()

    def test_resolving_to_multiple_objects_raises(self):
        service_already_used = self.api_groups[0].ztc_service
        ZGWApiGroupConfigFactory(
            ztc_service=service_already_used,
        )

        with self.assertRaises(ZGWApiGroupConfig.MultipleObjectsReturned):
            ZGWApiGroupConfig.objects.resolve_group_from_hints(
                service=service_already_used
            )


@requests_mock.Mocker()
class MultiZgwClientProxyTests(PlainTestCase):
    class SimpleClient:
        def __init__(self, url):
            self.url = url

        def fetch_rows(self):
            resp = requests.get(self.url)
            return resp.json()

    def setUp(self):
        self.a_client = self.SimpleClient("http://foo/bar/rows")
        self.another_client = self.SimpleClient("http://bar/baz/rows")

    def test_accessing_non_existent_methods_raises(self, m):
        proxy = MultiZgwClientProxy([self.a_client, self.another_client])

        with self.assertRaises(AttributeError) as cm:
            proxy.non_existent()

        self.assertEqual(
            str(cm.exception), "Method `non_existent` does not exist on the clients"
        )

    def test_all_successful_responses_are_returned(self, m):
        m.get(self.a_client.url, json=["foo", "bar"])
        m.get(self.another_client.url, json=["bar", "baz"])
        proxy = MultiZgwClientProxy([self.a_client, self.another_client])

        result = proxy.fetch_rows()

        self.assertEqual(
            result,
            MultiZgwClientProxyResult(
                responses=[
                    ZgwClientResponse(
                        client=self.a_client, result=["foo", "bar"], exception=None
                    ),
                    ZgwClientResponse(
                        client=self.another_client,
                        result=["bar", "baz"],
                        exception=None,
                    ),
                ]
            ),
        )
        self.assertEqual(result.responses, result.successful_responses)
        self.assertEqual(result.failing_responses, [])
        self.assertEqual(result.join_results(), ["foo", "bar", "bar", "baz"])
        self.assertEqual(
            result.raise_on_failures(),
            None,
            msg="raise_on_failures is a noop if all responses are successful",
        )

    def test_ruthy_results_ignores_falsy_results(self, m):
        truthy_client = Mock()
        truthy_client.fetch_result.return_value = "foobar"

        falsy_values = (None, "", [], tuple(), set(), 0)
        for falsy_value in falsy_values:
            with self.subTest(f"falsy value: {falsy_value}"):
                falsy_client = Mock()
                falsy_client.fetch_result.return_value = falsy_value
                proxy = MultiZgwClientProxy([truthy_client, falsy_client])
                result = proxy.fetch_result()
                self.assertEqual(
                    result.truthy_responses,
                    [
                        ZgwClientResponse(
                            client=truthy_client, result="foobar", exception=None
                        )
                    ],
                )

    def test_join_truthy_results_ignores_failing_results(self, m):
        truthy_client = Mock()
        truthy_client.fetch_result.return_value = "foobar"

        falsy_values = (None, "", [], tuple(), set(), 0)
        for falsy_value in falsy_values:
            with self.subTest(f"falsy value: {falsy_value}"):
                falsy_client = Mock()
                falsy_client.fetch_result.side_effect = [
                    *falsy_values,
                    ValueError("Bad stuff"),
                ]
                proxy = MultiZgwClientProxy([truthy_client, falsy_client])
                result = proxy.fetch_result()
                self.assertEqual(
                    result.truthy_responses,
                    [
                        ZgwClientResponse(
                            client=truthy_client, result="foobar", exception=None
                        )
                    ],
                )

    def test_partial_exceptions_are_returned(self, m):
        m.get(self.a_client.url, json=["foo", "bar"])
        # Second client will raise an exception
        m.get(self.another_client.url, exc=requests.exceptions.Timeout)

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

        # It's non-trivial to compare exceptions on equality, so we have to validate the
        # object in steps
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
        m.get(self.a_client.url, json=["foo", "bar"])
        m.get(self.another_client.url, json=["bar", "baz"])
        proxy = MultiZgwClientProxy([self.a_client, self.another_client])

        result = proxy.fetch_rows()

        # Verify that each invocation yields a fresh generator with a clean iteration state
        for _ in range(2):
            self.assertEqual(
                [row.result for row in result], [["foo", "bar"], ["bar", "baz"]]
            )

    def test_response_iterator_includes_failing_responses(self, m):
        m.get(self.a_client.url, json=["foo", "bar"])
        m.get(self.another_client.url, exc=requests.exceptions.Timeout)

        proxy = MultiZgwClientProxy([self.a_client, self.another_client])
        result = proxy.fetch_rows()

        self.assertEqual([row.exception is None for row in result], [True, False])
