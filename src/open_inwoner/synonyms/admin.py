from django.contrib import admin

from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from import_export.admin import ImportExportMixin
from import_export.formats import base_formats

from .models import Synonym
from .resources import SynonymResource


@admin.register(Synonym)
class SynonymAdmin(ImportExportMixin, admin.ModelAdmin, DynamicArrayMixin):
    list_display = ("term", "synonyms")
    resource_class = SynonymResource
    formats = [base_formats.CSV]
