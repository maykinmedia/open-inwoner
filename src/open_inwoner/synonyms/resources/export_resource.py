from import_export import fields, resources
from import_export.widgets import SimpleArrayWidget

from ..models import Synonym


class SynonymExportResource(resources.ModelResource):
    term = fields.Field(column_name="Term", attribute="term")
    synonyms = fields.Field(
        column_name="UF",
        attribute="synonyms",
        widget=SimpleArrayWidget(),
    )

    class Meta:
        model = Synonym
        fields = ("term", "synonyms")
        export_order = ("term", "synonyms")
