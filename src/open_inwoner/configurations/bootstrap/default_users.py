import warnings

from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.models import ConfigurationModel

from open_inwoner.accounts.models import User


class UserConfigurationItem(ConfigurationModel):
    """
    Configuration model for a setting standard default users.
    """

    class Meta:
        django_model_refs = {
            User: (
                "email",
                "password",
                "is_staff",
                "is_superuser",
            )
        }


class UserConfigurationModel(ConfigurationModel):
    users: list[UserConfigurationItem]


class UserConfigurationStep(BaseConfigurationStep):
    """
    Creates or updates a one or more default users based on
    YAML settings. Note that a provided password
    will only be used if the user does not exist yet.
    """

    verbose_name = "User Configuration Step"
    enable_setting = "default_user_configuration_enable"
    config_model = UserConfigurationModel
    namespace = "default_user_configuration_config"

    def execute(self, model):
        for user_item in model.users:
            user, created = User.objects.update_or_create(
                email=user_item.email,
                defaults={
                    "email": user_item.email,
                    "is_staff": user_item.is_staff,
                    "is_superuser": user_item.is_superuser,
                },
            )

            if created:
                user.set_password(user_item.password)

            user.save()

            if user.check_password(user_item.password):
                warnings.warn(
                    "\nThe password for the automatically created "
                    f"user '{user_item.email}' is currently set to a hardcoded default. "
                    "Make sure to change the password in the admin panel.\n\n"
                )
