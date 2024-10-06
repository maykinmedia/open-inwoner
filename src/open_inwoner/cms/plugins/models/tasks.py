import json

from django.db import models
from django.utils.translation import gettext_lazy as _

import requests
from cms.models import CMSPlugin
from objectsapiclient.models import Configuration, ObjectTypeField
from zgw_consumers.constants import APITypes


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

    def get_tasks(self):
        # TODO: note that this filters client-side, better would be to filter this
        # in the Objects API GET-request using data_attr
        return [
            obj.record["data"]
            for obj in Configuration.get_solo().client.get_objects(
                object_type_uuid=self.object_type
            )
        ]

    def get_tasks_by_bsn(self, bsn):
        tasks = []
        for task in self.get_tasks():
            identificatie = task["identificatie"]
            if not identificatie or identificatie["type"] != "bsn":
                continue
            task_bsn = identificatie["value"]
            if task_bsn and task_bsn == bsn:
                tasks += [task]
        return tasks
