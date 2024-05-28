from django.core.management import call_command
from django.test import TestCase

from open_inwoner.accounts.apps import update_admin_index


class FixtureTests(TestCase):
    def test_admin_index(self):
        self.assertTrue(update_admin_index())

    def test_cms_pages(self):
        # pass if this doesn't raise anything
        call_command("loaddata", "cms-pages")

    def test_custom_csp(self):
        # pass if this doesn't raise anything
        call_command("loaddata", "custom_csp")

    def test_mail_editor(self):
        # pass if this doesn't raise anything
        call_command("loaddata", "mail-editor")

    def test_profile_apphook_config(self):
        # pass if this doesn't raise anything
        call_command("loaddata", "profile_apphook_config")
