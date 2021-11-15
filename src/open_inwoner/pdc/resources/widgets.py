from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from import_export.widgets import ManyToManyWidget


class ValidatedManyToManyWidget(ManyToManyWidget):
    def clean(self, value, row=None, *args, **kwargs):
        if self.model.__name__ == "Category" and value == "":
            raise ValidationError(_("The field categories is required"))

        qs = super().clean(value, row=row, *args, **kwargs)
        if not qs and value != "":
            raise ValidationError(
                _(f"The {self.model.__name__.lower()} you entered does not exist")
            )
        return qs
