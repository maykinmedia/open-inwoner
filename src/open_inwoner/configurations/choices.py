from django.db import models
from django.utils.translation import ugettext_lazy as _


class ColorTypeChoices(models.TextChoices):
    light = "#FFFFFF", _("light")
    dark = "#4B4B4B", _("dark")


class OpenIDDisplayChoices(models.TextChoices):
    admin = "admin", _("Admin")
    regular = "regular", _("Regular user")


class CustomFontName(models.TextChoices):
    body = _("text_body_font"), _("Text body font")
    heading = _("heading_font"), _("Heading font")
