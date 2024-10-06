from django.db import models
from django.utils.translation import gettext_lazy as _

from cms.models import CMSPlugin
from objectsapiclient.models import ObjectTypeField


class TasksConfig(CMSPlugin):
    title = models.CharField(
        _("Title"),
        max_length=250,
        help_text=_("The title of the tasks block"),
        default=_("Mijn Taken"),
    )
    object_type = ObjectTypeField()  # Stores the UUID of the selected object_type

    def __str__(self):
        return self.title or super().__str__()
