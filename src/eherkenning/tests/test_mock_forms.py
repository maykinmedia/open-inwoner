from django.test import TestCase, modify_settings, override_settings

from eherkenning.mock.idp.forms import eHerkenningPasswordLoginForm


class PasswordFormTestCase(TestCase):
    def test_password_login_form_validate(self):
        scenarios = [
            ("29664887", "password", False, False),  # OK
            ("abcdefgh", "password", True, False),  # kvk wrong type
            ("296648875", "password", True, False),  # kvk too long
            ("2966488", "password", True, False),  # kvk too short
            ("29664887", "", False, True),  # missing password
        ]

        for auth_name, auth_pass, name_has_error, pass_has_error in scenarios:
            with self.subTest(auth_name=auth_name):
                form = eHerkenningPasswordLoginForm(
                    data={"auth_name": auth_name, "auth_pass": auth_pass}
                )

                self.assertEqual(form.has_error("auth_name"), name_has_error)
                self.assertEqual(form.has_error("auth_pass"), pass_has_error)
                self.assertEqual(
                    form.is_valid(), not (name_has_error or pass_has_error)
                )
