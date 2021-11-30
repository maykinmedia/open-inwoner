from import_export import fields, resources

from ..models import Synonym
from .widgets import CustomSimpleArrayWidget


class SynonymImportResource(resources.ModelResource):
    term = fields.Field(column_name="Term", attribute="term")
    synonyms = fields.Field(
        column_name="UF",
        attribute="synonyms",
        widget=CustomSimpleArrayWidget(separator="|"),
    )

    class Meta:
        model = Synonym
        clean_model_instances = True
        import_id_fields = ("term",)
        fields = ("term", "synonyms")
