from unittest.mock import patch

from django.test import TestCase

from pyquery import PyQuery as PQ

from open_inwoner.cms.profile.cms_apps import ProfileApphook
from open_inwoner.cms.tests import cms_tools
from open_inwoner.configurations.models import SiteConfiguration


class KCMSurveyTestCase(TestCase):
    css_selector = ".kcm-survey"

    def setUp(self):
        cms_tools.create_apphook_page(ProfileApphook)

    @patch(
        "open_inwoner.configurations.models.SiteConfiguration.get_solo",
        return_value=SiteConfiguration(
            kcm_survey_link_text="Geef je mening",
            kcm_survey_link_url="https://some-kcm-survey.url/foo",
        ),
    )
    def test_kcm_survey_configured(self, mock_config):
        response = self.client.get("/")

        doc = PQ(response.content)

        self.assertEqual(len(doc.find(self.css_selector)), 1)

    def test_kcm_survey_not_configured(self):
        invalid_configs = (
            ("Geef je mening", ""),
            ("", "https://some-kcm-survey.url/foo"),
            ("", ""),
        )
        for text, url in invalid_configs:
            with self.subTest(text=text, url=url):

                with patch(
                    "open_inwoner.configurations.models.SiteConfiguration.get_solo",
                    return_value=SiteConfiguration(
                        kcm_survey_link_text=text, kcm_survey_link_url=url
                    ),
                ):
                    response = self.client.get("/")

                    doc = PQ(response.content)

                    self.assertEqual(len(doc.find(self.css_selector)), 0)
