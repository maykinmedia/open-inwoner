from django.contrib.gis.db.models import PointField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

from geopy.exc import GeopyError
from localflavor.nl.models import NLZipCodeField

from .geocode import geocode_address


class GeoModel(models.Model):
    street = models.CharField(
        _("street"), blank=True, max_length=250, help_text=_("Address street")
    )
    housenumber = models.CharField(
        _("house number"),
        blank=True,
        max_length=250,
        help_text=_("Address house number"),
    )
    postcode = NLZipCodeField(_("postcode"), help_text=_("Address postcode"))
    city = models.CharField(_("city"), max_length=250, help_text=_("Address city"))
    geometry = PointField(
        _("geometry"),
        help_text=_("Geo coordinates of the location"),
    )

    class Meta:
        abstract = True

    @property
    def address_str(self):
        # geocoding doesn't work if postcode has space inside
        postcode = self.postcode.replace(" ", "")
        return f"{self.street} {self.housenumber}, {postcode} {self.city}"

    def clean(self):
        super().clean()

        self.clean_geometry()

    def clean_geometry(self):
        model = self.__class__
        # # if address is not changed - do nothing
        if self.id and self.address_str == model.objects.get(id=self.id).address_str:
            return

        # locate geo coordinates using address string
        try:
            geometry = geocode_address(self.address_str)
        except GeopyError as exc:
            raise ValidationError(
                _("Locating geo coordinates has failed: %(exc)s") % {"exc": exc}
            )

        if not geometry:
            raise ValidationError(
                _(
                    "Geo coordinates of the address can't be found. "
                    "Make sure that the address data are correct"
                )
            )
        self.geometry = geometry
