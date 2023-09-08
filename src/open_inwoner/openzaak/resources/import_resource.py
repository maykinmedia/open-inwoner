from django.utils.translation import ugettext_lazy as _

from import_export import fields, resources
from import_export.exceptions import ImportExportError

from open_inwoner.openzaak.models import StatusTranslation


class StatusTranslationImportResource(resources.ModelResource):
    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        # Validate that file contains all the headers
        missing_headers = set(self.get_diff_headers()) - set(dataset.headers)
        if missing_headers:
            missing_headers = ",\n".join(missing_headers)
            raise ImportExportError(_(f"Missing required headers: {missing_headers}"))

        return super().before_import(dataset, using_transactions, dry_run, **kwargs)

    def get_or_init_instance(self, instance_loader, row):
        # Replace newlines from excel
        for key, value in row.items():
            if isinstance(value, str):
                row[key] = value.replace("_x000D_", "\n")

        return super().get_or_init_instance(instance_loader, row)

    status = fields.Field(column_name="status", attribute="status")
    translation = fields.Field(column_name="translation", attribute="translation")

    class Meta:
        model = StatusTranslation
        import_id_fields = ("status",)
        fields = ("status", "translation")
