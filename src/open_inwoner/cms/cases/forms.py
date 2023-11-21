import os

from django import forms
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import gettext_lazy as _

from open_inwoner.openzaak.models import (
    OpenZaakConfig,
    ZaakTypeConfig,
    ZaakTypeInformatieObjectTypeConfig,
)


class CaseUploadForm(forms.Form):
    type = forms.ModelChoiceField(
        ZaakTypeInformatieObjectTypeConfig.objects.none(),
        empty_label=None,
        label=_("Bestand type"),
    )
    file = forms.FileField(label=_("Bestand"), required=True)

    def __init__(self, case, **kwargs):
        self.oz_config = OpenZaakConfig.get_solo()
        super().__init__(**kwargs)

        help_text = f"Grootte max. { self.oz_config.max_upload_size } MB, toegestane document formaten: { ', '.join(self.oz_config.allowed_file_extensions) }."

        try:
            ztc = ZaakTypeConfig.objects.filter_case_type(case.zaaktype).get()
            help_text = ztc.description or help_text
        except (AttributeError, ObjectDoesNotExist):
            pass

        self.fields["file"].help_text = help_text

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

        max_allowed_size = 1024**2 * self.oz_config.max_upload_size
        allowed_extensions = sorted(self.oz_config.allowed_file_extensions)
        filename, file_extension = os.path.splitext(file.name)

        if file.size > max_allowed_size:
            raise ValidationError(
                f"Een aangeleverd bestand dient maximaal {self.oz_config.max_upload_size} MB te zijn, uw bestand is te groot."
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
