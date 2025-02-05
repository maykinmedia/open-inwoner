from django.test import TestCase
from django.utils.translation import gettext as _

from open_inwoner.cms.footer.cms_plugins import FooterPagesPlugin
from open_inwoner.cms.tests import cms_tools
from open_inwoner.openklant.constants import KlantenServiceType
from open_inwoner.openklant.models import ESuiteKlantConfig, KlantenSysteemConfig
from open_inwoner.openklant.tests.factories import ContactFormSubjectFactory
from open_inwoner.utils.test import ClearCachesMixin


class ContactFormTestCase(ClearCachesMixin, TestCase):
    def setUp(self):
        super().setUp()

        # clear esuite_config
        esuite_config = ESuiteKlantConfig.get_solo()
        esuite_config.klanten_service = None
        esuite_config.contactmomenten_service = None
        esuite_config.register_bronorganisatie_rsin = ""
        esuite_config.register_type = ""
        esuite_config.register_employee_id = ""
        esuite_config.save()

    def test_no_form_link_shown_in_footer_if_not_has_configuration(self):
        # set nothing
        klant_config = KlantenSysteemConfig.get_solo()
        self.assertFalse(klant_config.has_contactform_configuration)

        html, context = cms_tools.render_plugin(FooterPagesPlugin)

        self.assertNotIn(_("Contact formulier"), html)

    def test_form_link_is_shown_in_footer_when_has_configuration(self):
        klant_config = KlantenSysteemConfig.get_solo()
        klant_config.primary_backend = KlantenServiceType.ESUITE.value
        klant_config.save()

        self.assertFalse(klant_config.has_contactform_configuration)

        esuite_config = ESuiteKlantConfig.get_solo()
        ContactFormSubjectFactory(esuite_config=esuite_config)

        klant_config.register_contact_email = "example@example.com"
        klant_config.save()

        self.assertTrue(klant_config.has_contactform_configuration)

        html, context = cms_tools.render_plugin(FooterPagesPlugin)

        self.assertIn(_("Contact formulier"), html)
