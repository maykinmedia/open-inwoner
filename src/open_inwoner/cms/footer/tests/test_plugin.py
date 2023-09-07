from django.test import TestCase
from django.utils.translation import gettext as _

from open_inwoner.cms.footer.cms_plugins import FooterPagesPlugin
from open_inwoner.cms.tests import cms_tools
from open_inwoner.openklant.models import OpenKlantConfig
from open_inwoner.openklant.tests.factories import ContactFormSubjectFactory
from open_inwoner.utils.test import ClearCachesMixin


class ContactFormTestCase(ClearCachesMixin, TestCase):
    def setUp(self):
        super().setUp()
        # clear config
        config = OpenKlantConfig.get_solo()
        config.klanten_service = None
        config.contactmomenten_service = None
        config.register_email = ""
        config.register_contact_moment = False
        config.register_bronorganisatie_rsin = ""
        config.register_type = ""
        config.register_employee_id = ""
        config.save()

    def test_no_form_link_shown_in_footer_if_not_has_configuration(self):
        # set nothing
        config = OpenKlantConfig.get_solo()
        self.assertFalse(config.has_form_configuration())

        html, context = cms_tools.render_plugin(FooterPagesPlugin)

        self.assertNotIn(_("Contact formulier"), html)

    def test_form_link_is_shown_in_footer_when_has_configuration(self):
        ok_config = OpenKlantConfig.get_solo()
        self.assertFalse(ok_config.has_form_configuration())

        ContactFormSubjectFactory(config=ok_config)

        ok_config.register_email = "example@example.com"
        ok_config.save()

        self.assertTrue(ok_config.has_form_configuration())

        html, context = cms_tools.render_plugin(FooterPagesPlugin)

        self.assertIn(_("Contact formulier"), html)
