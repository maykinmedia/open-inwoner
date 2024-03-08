from django.db import models
from django.utils.translation import gettext_lazy as _

from requests.auth import HTTPBasicAuth
from solo.models import SingletonModel


class LapostaConfig(SingletonModel):
    api_root = models.URLField(
        verbose_name=_("API root"),
        max_length=128,
        help_text=_(
            "The root of the API with version number (e.g. https://api.laposta.nl/v2/)."
        ),
    )
    basic_auth_username = models.CharField(
        verbose_name=_("Basic Authentication username"),
        max_length=255,
        blank=True,
        help_text=_("The username used to authenticate with the Laposta API."),
    )
    basic_auth_password = models.CharField(
        verbose_name=_("Basic Authentication password"),
        max_length=255,
        blank=True,
        help_text=_("The password used to authenticate with the Laposta API"),
    )

    class Meta:
        verbose_name = _("Laposta configuration")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(api_root={self.api_root})"

    # Methods required to configure `ape_pie.APIClient`
    def get_client_base_url(self) -> str:
        return self.api_root

    def get_client_session_kwargs(self) -> dict[str, HTTPBasicAuth]:
        return {
            "auth": HTTPBasicAuth(self.basic_auth_username, self.basic_auth_password)
        }
