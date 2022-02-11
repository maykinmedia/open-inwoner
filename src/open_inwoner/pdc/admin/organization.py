from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from ..models import Organization, OrganizationType
from .mixins import GeoAdminMixin


@admin.register(Organization)
class OrganizationAdmin(GeoAdminMixin, admin.ModelAdmin):
    # List
    list_display = ("name", "type")
    list_filter = ("type__name", "city")
    search_fields = ("name",)
    ordering = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    # Detail
    fieldsets = (
        (None, {"fields": ("name", "slug", "type", "logo", "neighbourhood")}),
        (_("Contact"), {"fields": ("email", "phonenumber")}),
        (
            _("Address"),
            {"fields": ("street", "housenumber", "postcode", "city", "geometry")},
        ),
    )


@admin.register(OrganizationType)
class OrganizationTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
