import os

from django.db import models
from django.utils.translation import ugettext_lazy as _

from cms.models import CMSPlugin
from objectsapiclient.models import Configuration, ObjectTypeField


class ObjectsList(CMSPlugin):
    title = models.CharField(_("Title"), max_length=250)
    object_type = ObjectTypeField()  # Stores the UUID of the selected object_type

    def get_objects(self):
        return Configuration.get_solo().client.get_objects(
            object_type_uuid=self.object_type
        )

    def __str__(self):
        return self.title
