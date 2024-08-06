from django.contrib.messages import get_messages
from django.test import TestCase, override_settings
from django.urls import reverse

from open_inwoner.openzaak.tests.factories import ZGWApiGroupConfigFactory


@override_settings(
    ROOT_URLCONF="open_inwoner.cms.tests.urls",
)
class LegacyCaseDetailUrlRedirectTest(TestCase):
    def test_legacy_url_redirects_to_only_api_group_prefix(self):
        sole_api_group = ZGWApiGroupConfigFactory()

        object_id = "test_object_id"
        legacy_handler_url = reverse(
            "cases:legacy_case_detail",
            kwargs={"object_id": object_id},
        )
        target_url = reverse(
            "cases:case_detail",
            kwargs={"api_group_id": sole_api_group.id, "object_id": object_id},
        )

        response = self.client.get(legacy_handler_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], target_url)

    def test_legacy_url_redirects_to_case_list_when_multiple_api_groups(self):
        ZGWApiGroupConfigFactory(), ZGWApiGroupConfigFactory()

        object_id = "test_object_id"
        legacy_handler_url = reverse(
            "cases:legacy_case_detail",
            kwargs={"object_id": object_id},
        )
        target_url = reverse("cases:index")

        response = self.client.get(legacy_handler_url)
        messages = [str(m) for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], target_url)
        self.assertEqual(
            messages,
            [
                "The link you clicked on has expired. Please find your case in the"
                " list below."
            ],
        )

    def test_legacy_url_redirect_returns_404_on_missing_api_groups(self):
        object_id = "test_object_id"
        legacy_handler_url = reverse(
            "cases:legacy_case_detail",
            kwargs={"object_id": object_id},
        )

        legacy_handler_url = reverse(
            "cases:legacy_case_detail",
            kwargs={"object_id": object_id},
        )

        response = self.client.get(legacy_handler_url)
        self.assertEqual(response.status_code, 404)
