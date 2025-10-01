from django.test import TestCase

from open_inwoner.accounts.forms import CustomRegistrationForm, UserForm
from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.configurations.models import SiteConfiguration


class RegistrationFormTest(TestCase):
    def test_validation_phonenumber_alt(self):
        config = SiteConfiguration.get_solo()
        config.login_2fa_sms = True
        config.save()

        form = CustomRegistrationForm(
            data={
                "phonenumber": "",
                "phonenumber_alternative": "0612345678",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("phonenumber_alternative", form.errors)


class UserFormTest(TestCase):
    def test_validation_phonenumber_alt(self):
        user = UserFactory()
        form = UserForm(
            user=user,
            data={
                "phonenumber": "",
                "phonenumber_alternative": "0612345678",
            },
        )

        self.assertFalse(form.is_valid())
        self.assertIn("phonenumber_alternative", form.errors)
