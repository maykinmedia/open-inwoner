from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from django_prosemirror.config import ProsemirrorConfig
from django_prosemirror.schema import MarkType, NodeType
from django_prosemirror.serde import html_to_doc
from import_export.widgets import ManyToManyWidget, Widget


class ValidatedManyToManyWidget(ManyToManyWidget):
    def clean(self, value, row=None, *args, **kwargs):
        if self.model.__name__ == "Category" and not value:
            raise ValidationError(_("The field categories is required"))

        qs = super().clean(value, row=row, *args, **kwargs)
        if value and not qs:
            raise ValidationError(
                _("The {model_name} you entered does not exist").format(
                    model_name=self.model.__name__.lower()
                )
            )
        return qs


class ProsemirrorWidget(Widget):
    """
    Widget for handling ProsemirrorFieldDocument fields in import/export.
    """

    def render(self, value, obj=None):
        """Export ProsemirrorFieldDocument as HTML string."""
        if value is None or value == "":
            return ""
        # ProsemirrorFieldDocument has a doc attribute (use this to avoid triggering html property on invalid data)
        if hasattr(value, "doc") and value.doc:
            return value.html
        # For string values, return as-is
        return str(value) if value else ""

    def clean(self, value, row=None, *args, **kwargs):
        """
        Import HTML string and convert to ProseMirror JSON document.

        The field expects a dict with ProseMirror JSON structure, not HTML string.
        """
        if not value or not value.strip():
            return None

        # Convert HTML to ProseMirror JSON document
        # Use a basic config that matches what most fields use
        config = ProsemirrorConfig(
            allowed_node_types=[
                NodeType.PARAGRAPH,
                NodeType.HEADING,
                NodeType.FILER_IMAGE,
            ],
            allowed_mark_types=[
                MarkType.STRONG,
                MarkType.ITALIC,
                MarkType.LINK,
                MarkType.UNDERLINE,
            ],
        )

        try:
            # html_to_doc returns a dict with ProseMirror JSON structure
            doc = html_to_doc(value, schema=config.schema)
            return doc
        except Exception:
            # If conversion fails, return None
            return None
