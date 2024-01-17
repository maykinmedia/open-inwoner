from django.db import models
from django.utils.translation import ugettext_lazy as _


class FontFileName(models.TextChoices):
    body = _("text_body_font"), _("Text body font")
    heading = _("heading_font"), _("Heading font")
