from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from cms.models import CMSPlugin
from objectsapiclient.models import LazyObjectTypeField

MIN_CASES = 1
MAX_CASES_DEFAULT = 10


class TakenPluginConfig(CMSPlugin):
    class Meta:
        app_label = "plugins"
        db_table = "plugins_tasksconfig"  # Use existing table from legacy plugins app

    title = models.CharField(
        _("Title"),
        max_length=250,
        help_text=_("The title of the tasks block"),
        default=_("Mijn Taken"),
    )

    # The two kinds of object types come from the same API,
    # but they are based on independent schemata
    object_type_dimpact = LazyObjectTypeField(
        verbose_name=_("Object Type (Extern Formulier Taak)"),
        null=True,
        blank=True,
    )
    object_type_generieke_dienstverlening = LazyObjectTypeField(
        verbose_name=_("Object Type (Url Taak)"),
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.title or super().__str__()


class ZakenPluginConfig(CMSPlugin):
    class Meta:
        app_label = "plugins"
        db_table = (
            "plugins_cmszakenpluginconfig"  # Use existing table from legacy plugins app
        )

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


__all__ = [
    "TakenPluginConfig",
    "ZakenPluginConfig",
    "MIN_CASES",
    "MAX_CASES_DEFAULT",
]
