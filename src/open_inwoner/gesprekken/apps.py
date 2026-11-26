from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class GesprekkenAppConfig(AppConfig):
    name = "open_inwoner.gesprekken"
    verbose_name = _("Mijn gesprekken")
