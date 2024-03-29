from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from import_export.widgets import ManyToManyWidget


class ValidatedManyToManyWidget(ManyToManyWidget):
    def clean(self, value, row=None, *args, **kwargs):
        if self.model.__name__ == "Category" and not value:
            raise ValidationError(_("The field categories is required"))

        qs = super().clean(value, row=row, *args, **kwargs)
        if value and not qs:
            raise ValidationError(
                _(f"The {self.model.__name__.lower()} you entered does not exist")
            )
        return qs
