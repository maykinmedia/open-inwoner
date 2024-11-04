from django.core.management import call_command
from django.db.models.signals import post_migrate
from django.test import TestCase, override_settings

from open_inwoner.accounts.apps import update_admin_index


class FixtureTests(TestCase):
    def test_admin_index(self):
        call_command("loaddata", "django-admin-index")

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


class AutoLoadDjangoAdminIndexFixtureTests(TestCase):
    def test_update_admin_index_hook_is_not_registered_if_skip_flag_is_unset(self):
        self.assertTrue(update_admin_index())

    @override_settings(SKIP_ADMIN_INDEX_FIXTURE=False)
    def test_update_admin_index_hook_is_not_registered_if_skip_flag_is_false(self):
        self.assertTrue(update_admin_index())

    @override_settings(SKIP_ADMIN_INDEX_FIXTURE=True)
    def test_update_admin_index_hook_is_registered_if_skip_flag_is_true(self):
        self.assertFalse(update_admin_index())

    def test_update_admin_index_hook_is_registered(self):
        connected_functions = [receiver[1]() for receiver in post_migrate.receivers]
        self.assertIn(update_admin_index, connected_functions)
