from django.contrib import admin

from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from import_export.admin import ImportExportMixin
from import_export.formats import base_formats

from .models import Synonym
from .resources import SynonymExportResource, SynonymImportResource


@admin.register(Synonym)
class SynonymAdmin(ImportExportMixin, admin.ModelAdmin, DynamicArrayMixin):
    list_display = ("term", "synonyms")
    resource_class = SynonymImportResource
    formats = [base_formats.CSV]

    def get_export_resource_class(self):
        return SynonymExportResource
