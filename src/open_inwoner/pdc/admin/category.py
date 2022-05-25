from django.contrib import admin
from django.utils.translation import gettext as _

from import_export.admin import ImportExportMixin
from import_export.formats import base_formats
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from open_inwoner.utils.logentry import system_action

from ..models import Category
from ..resources import CategoryExportResource, CategoryImportResource
from .faq import QuestionInline


@admin.register(Category)
class CategoryAdmin(ImportExportMixin, TreeAdmin):
    change_list_template = "admin/category_change_list.html"
    form = movenodeform_factory(Category, fields="__all__")
    inlines = (QuestionInline,)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    ordering = ("path",)

    # import-export
    import_template_name = "admin/category_import.html"
    resource_class = CategoryImportResource
    formats = [base_formats.XLSX, base_formats.CSV]

    def get_export_resource_class(self):
        return CategoryExportResource

    def export_action(self, request, *args, **kwargs):
        response = super().export_action(request, *args, **kwargs)

        if request.method == "POST":
            user = request.user
            system_action(_("categories were exported"), user)

        return response
