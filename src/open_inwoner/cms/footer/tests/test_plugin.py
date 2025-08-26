from django.test import TestCase
from django.utils.translation import gettext as _

from open_inwoner.cms.footer.cms_plugins import FooterPagesPlugin
from open_inwoner.cms.tests import cms_tools
from open_inwoner.openklant.cms_apps import OpenklantApphook
from open_inwoner.openklant.constants import KlantenServiceType
from open_inwoner.openklant.models import ESuiteKlantConfig, KlantenSysteemConfig
from open_inwoner.openklant.tests.factories import ContactFormSubjectFactory
from open_inwoner.utils.test import ClearCachesMixin


class FooterPagesPluginTest(ClearCachesMixin, TestCase):
    def setUp(self):
        super().setUp()

        cms_tools.create_apphook_page(OpenklantApphook, title="Contactformulier")

        # clear esuite_config
        esuite_config = ESuiteKlantConfig.get_solo()
        esuite_config.klanten_service = None
        esuite_config.contactmomenten_service = None
        esuite_config.register_bronorganisatie_rsin = ""
        esuite_config.register_type = ""
        esuite_config.register_employee_id = ""
        esuite_config.save()

    def test_no_contactform_link_shown_in_footer_if_contactform_not_enabled(self):
        # set nothing
        klant_config = KlantenSysteemConfig.get_solo()
        self.assertFalse(klant_config.contact_registration_enabled)

        html, context = cms_tools.render_plugin(FooterPagesPlugin)

        self.assertNotIn(_("Contactformulier"), html)

    def test_contactform_link_shown_in_footer_if_contactform_enabled(self):
        klant_config = KlantenSysteemConfig.get_solo()
        klant_config.primary_backend = KlantenServiceType.ESUITE.value
        klant_config.save()

        self.assertFalse(klant_config.contact_registration_enabled)

        esuite_config = ESuiteKlantConfig.get_solo()
        ContactFormSubjectFactory(esuite_config=esuite_config)

        klant_config.register_contact_email = "example@example.com"
        klant_config.save()

        self.assertTrue(klant_config.contact_registration_enabled)

        html, context = cms_tools.render_plugin(FooterPagesPlugin)
