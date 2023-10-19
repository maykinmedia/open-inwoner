import os

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from open_inwoner.openzaak.models import (
    OpenZaakConfig,
    ZaakTypeInformatieObjectTypeConfig,
)
from open_inwoner.utils.validators import CharFieldValidator


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class CaseUploadForm(forms.Form):
    title = forms.CharField(
        label=_("Titel bestand"), max_length=255, validators=[CharFieldValidator()]
    )
    type = forms.ModelChoiceField(
        ZaakTypeInformatieObjectTypeConfig.objects.none(),
        empty_label=None,
        label=_("Bestand type"),
    )
    file = MultipleFileField(label=_("Bestand"))

    def __init__(self, case, **kwargs):
        super().__init__(**kwargs)

        if case:
            self.fields[
                "type"
            ].queryset = ZaakTypeInformatieObjectTypeConfig.objects.filter_enabled_for_case_type(
                case.zaaktype
            )

        choices = self.fields["type"].choices

        if choices and len(choices) == 1:
            self.fields["type"].initial = list(choices)[0][0].value
            self.fields["type"].widget = forms.HiddenInput()

    def clean_file(self):
        file = self.cleaned_data["file"]

        config = OpenZaakConfig.get_solo()
        max_allowed_size = 1024**2 * config.max_upload_size
        allowed_extensions = sorted(config.allowed_file_extensions)
        filename, file_extension = os.path.splitext(file.name)

        if file.size > max_allowed_size:
            raise ValidationError(
                f"Een aangeleverd bestand dient maximaal {config.max_upload_size} MB te zijn, uw bestand is te groot."
            )

        if file_extension.lower().replace(".", "") not in allowed_extensions:
            raise ValidationError(
                f"Het type bestand dat u hebt geüpload is ongeldig. Geldige bestandstypen zijn: {', '.join(allowed_extensions)}"
            )

        return file


class CaseContactForm(forms.Form):
    question = forms.CharField(
        label=_("Vraag"),
        max_length=1024,
        widget=forms.Textarea(attrs={"rows": "5"}),
        required=True,
    )
