from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from cms.models import CMSPlugin

MIN_CASES = 1
MAX_CASES_DEFAULT = 10


class CMSZakenPluginConfig(CMSPlugin):
    title = models.CharField(
        _("Title"),
        max_length=250,
        help_text=_("The title of the zaken plugin block"),
        default=_("Mijn Zaken"),
    )
    num_zaken = models.IntegerField(
        _("Number of zaken"),
        default=4,
        validators=[
            MinValueValidator(MIN_CASES),
            MaxValueValidator(MAX_CASES_DEFAULT),
        ],
        help_text=_("The number of zaken that are displayed in the plugin"),
    )
