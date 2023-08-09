from django.test import override_settings
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.pdc.tests.factories import ProductFactory

from ...cms.tests import cms_tools
from ..models import SiteConfiguration
from .factories import SiteConfigurationFactory


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestGlobalHelpContext(WebTest):
    """
    Tests for help texts which are defined globally via SiteConfiguration

    See /open_inwoner/cms/tests/test_page_options.py for help texts defined
    via specific CMS pages.
    """

    def setUp(self):
        self.user = UserFactory()
        self.product = ProductFactory()

        cms_tools.create_homepage()

    def test_default_help_text_on_search_page(self):
        response = self.app.get(reverse("search:search"))
        help_text = response.context.get("help_text")

        self.assertEquals(
            help_text,
            _("Op dit scherm kunt u zoeken naar de producten en diensten."),
        )

    def test_custom_help_text_on_search_page(self):
        SiteConfigurationFactory()
        config = SiteConfiguration.get_solo()
        response = self.app.get(reverse("search:search"))
        help_text = response.context.get("help_text")

        self.assertEquals(help_text, config.search_help_text)

    def test_default_help_text_on_questionnaire_page(self):
        response = self.app.get(reverse("products:questionnaire_list"))
        help_text = response.context.get("help_text")

        self.assertEquals(
            help_text,
            _(
                "Het onderdeel Zelfdiagnose stelt u in staat om met het beantwoorden van enkele vragen een advies te krijgen van de gemeente, met concrete vervolgstappen en producten en diensten. U kunt tevens uw antwoorden en het advies bewaren om met een begeleider van de gemeente te bespreken."
            ),
        )

    def test_custom_help_text_on_questionnaire_page(self):
        SiteConfigurationFactory()
        config = SiteConfiguration.get_solo()
        response = self.app.get(reverse("products:questionnaire_list"))
        help_text = response.context.get("help_text")

        self.assertEquals(help_text, config.questionnaire_help_text)
