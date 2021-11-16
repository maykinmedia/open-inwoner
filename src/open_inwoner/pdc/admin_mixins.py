from import_export.admin import ImportExportMixin
from import_export.formats import base_formats

from .resources import (
    CategoryExportResource,
    CategoryImportResource,
    ProductExportResource,
    ProductImportResource,
)


class CategoryImportExportMixin(ImportExportMixin):
    change_list_template = "admin/category_change_list.html"
    import_template_name = "admin/category_import.html"
    resource_class = CategoryImportResource

    def get_export_resource_class(self):
        return CategoryExportResource

    def get_import_formats(self):
        formats = (
            base_formats.CSV,
            base_formats.XLSX,
            base_formats.TSV,
            base_formats.JSON,
            base_formats.YAML,
        )
        return [f for f in formats if f().can_import()]

    def get_export_formats(self):
        formats = (
            base_formats.CSV,
            base_formats.XLSX,
            base_formats.TSV,
            base_formats.JSON,
            base_formats.YAML,
        )
        return [f for f in formats if f().can_import()]


class ProductImportExportMixin(ImportExportMixin):

    resource_class = ProductImportResource
    import_template_name = "admin/product_import.html"

    def get_export_resource_class(self):
        return ProductExportResource

    def get_import_formats(self):
        formats = (
            base_formats.CSV,
            base_formats.XLSX,
            base_formats.TSV,
            base_formats.JSON,
            base_formats.YAML,
        )
        return [f for f in formats if f().can_import()]

    def get_export_formats(self):
        formats = (
            base_formats.CSV,
            base_formats.XLSX,
            base_formats.TSV,
            base_formats.JSON,
            base_formats.YAML,
        )
        return [f for f in formats if f().can_import()]
