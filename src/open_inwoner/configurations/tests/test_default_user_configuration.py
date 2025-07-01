from django.conf import settings
from django.test import TestCase

from django_setup_configuration.test_utils import execute_single_step

from open_inwoner.accounts.models import User
from open_inwoner.configurations.bootstrap.default_users import UserConfigurationStep


class TestDefaultUsersStep(TestCase):
    def test_default_user_was_created(self):
        email = "admin@user.nl"
        password = "change_me"

        config = {
            "default_user_configuration_enable": True,
            "default_user_configuration_config": {
                "users": [
                    {
                        "email": email,
                        "is_staff": True,
                        "is_superuser": True,
                        "password": password,
                    }
                ]
            },
        }

        execute_single_step(UserConfigurationStep, object_source=config)

        self.assertEqual(User.objects.count(), 1)

        user = User.objects.get(email=email)
        self.assertTrue(user.check_password(password))
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_default_user_was_updated(self):
        email = "someuser@bar.com"
        default_password = "change_me"
        actual_password = "12345"
        existing_user = User(email=email, first_name="Foo", last_name="Bar")
        existing_user.set_password(actual_password)
        existing_user.save()

        self.assertTrue(existing_user.check_password(actual_password))
        self.assertFalse(existing_user.is_staff)
        self.assertFalse(existing_user.is_superuser)

        existing_user.is_staff = True
        existing_user.save()

        config = {
            "default_user_configuration_enable": True,
            "default_user_configuration_config": {
                "users": [
                    {
                        "email": email,
                        "is_staff": True,
                        "is_superuser": True,
                        "password": default_password,
                    }
                ]
            },
        }

        execute_single_step(UserConfigurationStep, object_source=config)
        existing_user.refresh_from_db()

        self.assertFalse(
            existing_user.check_password(default_password)
        )  # Should not have updated
        self.assertTrue(existing_user.is_staff)
        self.assertTrue(existing_user.is_superuser)

    def test_verify_current_configuration(self):
        try:
            execute_single_step(
                UserConfigurationStep,
                yaml_source=f"{settings.BASE_DIR}/docker/setup_configuration/data.yaml",
            )
        except Exception as e:
            self.fail(
                f"Failed to execute UserConfigurationStep with the current configuration. Error: {e}"
            )
