from django.core.management import call_command
from django.test import TestCase


class DjangoAdminIndexFixtureTestCase(TestCase):
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
