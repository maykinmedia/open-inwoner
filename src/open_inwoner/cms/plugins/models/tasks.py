from django.db import models
from django.utils.translation import gettext_lazy as _

from cms.models import CMSPlugin
from objectsapiclient.models import LazyObjectTypeField


class TasksConfig(CMSPlugin):
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
