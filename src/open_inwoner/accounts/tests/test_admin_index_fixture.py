from django.core.management import call_command
from django.db.models.signals import post_migrate
from django.test import TestCase, TransactionTestCase

from open_inwoner.accounts.apps import update_admin_index


class ManualLoadDjangoAdminIndexFixtureTestCase(TransactionTestCase):
    """This test case serves as a trigger to warn us when we forget to
    update the django-admin-index fixture."""

    def test_django_admin_fixture_can_be_successfully_loaded(self):
        try:
            call_command("loaddata", "django-admin-index.json", verbosity=0)
        except Exception as e:
            self.fail(
                "Failed to load the django-admin-index fixture: perhaps you forgot to update them? "
                f"Got error: {str(e)}"
            )


class AutoLoadDjangoAdminIndexFixtureTestCase(TestCase):
    def test_update_admin_index_hook_is_registered(self):
        connected_functions = [receiver[1]() for receiver in post_migrate.receivers]
        self.assertIn(update_admin_index, connected_functions)

    def test_update_admin_index_hook_returns_true(self):
        self.assertTrue(update_admin_index())
