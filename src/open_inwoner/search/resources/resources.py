from import_export import fields, resources
from import_export.widgets import SimpleArrayWidget

from ..models import Synonym


class SynonymResource(resources.ModelResource):
    term = fields.Field(column_name="Term", attribute="term")
    synonyms = fields.Field(
        column_name="UF",
        attribute="synonyms",
        widget=SimpleArrayWidget(separator="|"),
    )

    class Meta:
        model = Synonym
        clean_model_instances = True
        import_id_fields = ("term",)
        fields = ("term", "synonyms")
