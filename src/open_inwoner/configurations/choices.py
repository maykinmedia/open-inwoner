from django.db import models
from django.utils.translation import ugettext_lazy as _


class ColorTypeChoices(models.TextChoices):
    light = "#FFFFFF", _("light")
    dark = "#4B4B4B", _("dark")


class OpenIDDisplayChoices(models.TextChoices):
    admin = "admin", _("Admin")
    regular = "regular", _("Regular user")


class CustomFontName(models.TextChoices):
    body = _("body_font_regular"), _("Text body font")
    body_italic = _("body_font_italic"), _("Text body font italic")
    body_bold = _("body_font_bold"), _("Text body font bold")
    body_bold_italic = _("body_font_bold_italic"), _("Text body font bold italic")
    heading = _("heading_font"), _("Heading font")
