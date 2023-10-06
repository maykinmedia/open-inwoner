import json

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _

from cms.models import CMSPlugin
from glom import glom
from glom.core import PathAccessError, PathAssignError
from objectsapiclient.models import Configuration, ObjectTypeField

from .constants import ComponentChoices, DateOrderChoices, StatusChoices


class ObjectsList(CMSPlugin):
    title = models.CharField(_("Title"), max_length=250)
    object_type = ObjectTypeField()  # Stores the UUID of the selected object_type
    status = models.CharField(
        _("Status"),
        max_length=250,
        choices=StatusChoices.choices,
        blank=True,
    )
    component = models.CharField(
        _("Component"),
        max_length=30,
        choices=ComponentChoices.choices,
        default=ComponentChoices.link,
    )
    no_results_message = models.TextField(
        _("No results message"),
        help_text=_("Text message to tell the user that there are no results found"),
    )
    date_order = models.CharField(
        _("Date Order"),
        help_text=_("Order date on acending or decending."),
        max_length=1,
        choices=DateOrderChoices.choices,
        default=DateOrderChoices.descent,
    )
    map_lat = models.DecimalField(
        _("Map starting Latitude"), max_digits=9, decimal_places=6, default=52.1326
    )
    map_long = models.DecimalField(
        _("Map starting Longitude"), max_digits=9, decimal_places=6, default=5.2913
    )
    map_zoom_level = models.IntegerField(
        _("Map starting Longitude"),
        validators=[MaxValueValidator(18), MinValueValidator(1)],
        default=3,
    )
    bsn_path = models.CharField(
        _("BSN Path"),
        max_length=250,
        help_text=_(
            "The path to the bsn value from data, for example: 'identificatie.value'"
        ),
        blank=True,
    )
    object_title = models.CharField(
        _("Object Title"),
        max_length=250,
        default="data.title",
        help_text=_("The path to the title, for example: 'data.title'"),
    )
    object_date = models.CharField(
        _("Object Date"),
        max_length=250,
        default="start_at",
        help_text=_("The path to the date, for example: 'start_at'"),
    )
    object_link = models.CharField(
        _("Object Link"),
        max_length=250,
        default="data.formulier.value",
        help_text=_("The path to the url, for example: 'data.formulier.value'"),
    )

    def _return_self(self):
        return f"{self.title}, {self.object_type}, {self.bsn_path}"

    def get_objects(self):
        return Configuration.get_solo().client.get_objects(
            object_type_uuid=self.object_type
        )

    def get_objects_by_bsn(self, bsn):
        data_attrs = []
        if self.object_type and self.bsn_path:
            data_attrs.append(
                "__".join(self.bsn_path.split(".")) + "__exact__" + str(bsn)
            )
            if self.status:
                data_attrs.append("status__exact__" + self.status)

            return Configuration.get_solo().client.get_objects_by_bsn(
                object_type_uuid=self.object_type,
                ordering=self.date_order + "record__startAt",
                data_attrs=",".join(data_attrs),
            )

    def convert_objects_to_actiondata(self, objects):
        object_list = []
        if objects:
            for object in objects:
                try:
                    object_list.append(
                        {
                            "title": glom(object.record, self.object_title),
                            "date": glom(object.record, self.object_date),
                            "link": glom(object.record, self.object_link),
                        }
                    )
                except (PathAccessError, PathAssignError):
                    pass

        return object_list

    def convert_objects_to_geodata(self, objects):
        features = []
        if objects:
            for object in objects:
                if geometry := object.record.get("geometry"):
                    try:
                        features.append(
                            {
                                "type": "Feature",
                                "geometry": geometry,
                                "properties": {
                                    "name": glom(object.record, self.object_title),
                                    "date": glom(object.record, self.object_date),
                                    "link": glom(object.record, self.object_link),
                                },
                            }
                        )
                    except (PathAccessError, PathAssignError):
                        pass

        return json.dumps(
            {
                "type": "FeatureCollection",
                "features": features,
            }
        )

    def __str__(self):
        return self.title
