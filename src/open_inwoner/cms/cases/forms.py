import os

from django import forms
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import gettext_lazy as _

from open_inwoner.openzaak.models import (
    OpenZaakConfig,
    ZaakTypeConfig,
    ZaakTypeInformatieObjectTypeConfig,
)
from open_inwoner.utils.forms import MultipleFileField


class CaseUploadForm(forms.Form):
    type = forms.ModelChoiceField(
        ZaakTypeInformatieObjectTypeConfig.objects.none(),
        empty_label=None,
        label=_("Bestand type"),
    )
    files = MultipleFileField(label=_("Bestand"))

    def __init__(self, case, **kwargs):
        self.oz_config = OpenZaakConfig.get_solo()
        super().__init__(**kwargs)

        help_text = f"Grootte max. {self.oz_config.max_upload_size} MB, toegestane document formaten: {', '.join(self.oz_config.allowed_file_extensions)}."

        try:
            ztc = ZaakTypeConfig.objects.filter_case_type(case.zaaktype).get()
            help_text = ztc.description or help_text
        except (AttributeError, ObjectDoesNotExist):
            pass

        self.fields["files"].help_text = help_text

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

    def clean_files(self):
        files = self.files.getlist("file")

        max_allowed_size = 1024 ** 2 * self.oz_config.max_upload_size
        allowed_extensions = sorted(self.oz_config.allowed_file_extensions)

        cleaned_files = []
        for file in files:
            filename, file_extension = os.path.splitext(file.name)

            if file.size > max_allowed_size:
                raise ValidationError(
                    f"Een aangeleverd bestand dient maximaal {self.oz_config.max_upload_size} MB te zijn, uw bestand is te groot."
                )

            if file_extension.lower().replace(".", "") not in allowed_extensions:
                raise ValidationError(
                    f"Het type bestand dat u hebt geüpload is ongeldig. Geldige bestandstypen zijn: {', '.join(allowed_extensions)}"
                )

            cleaned_files.append(file)

        return cleaned_files


class CaseContactForm(forms.Form):
    question = forms.CharField(
        label=_("Vraag"),
        max_length=1024,
        widget=forms.Textarea(attrs={"rows": "5"}),
        required=True,
    )


class CaseFilterForm(forms.Form):
    def __init__(
        self,
        status_freqs: dict[str, int],
        status_initial: list[str] | None = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.fields["status"].choices = (
            (status, f"{status} ({frequency})")
            for status, frequency in status_freqs.items()
        )
        self.fields["status"].initial = status_initial or []

    # note: not using widget but template here?
    status = forms.MultipleChoiceField(
        label=_("Filter by status"),
        widget=forms.Select(attrs={'id': 'choicewa'}),
        choices=dict(),
    )

# on base of simple checkbox
# class CaseFilterForm(forms.Form):
#     def __init__(
#         self,
#         *args,
#         status_freqs: dict[str, int] = None,
#         selected_statuses: list[str] = None,
#         **kwargs,
#     ):
#         # Extract status_freqs and selected_statuses from kwargs before calling the parent's init
#         super().__init__(*args, **kwargs)
#
#         if status_freqs is None:
#             status_freqs = {}
#
#         # Prepare choices for the multiselect checkbox
#         self.grouped_choices = [
#             {
#                 'status': status,
#                 'frequency': frequency,
#                 'checked': status in selected_statuses if selected_statuses else False,
#             }
#             for status, frequency in status_freqs.items()
#         ]
#
#         # Define the MultipleChoiceField after processing status_freqs
#         self.fields['status'].choices = [
#             (status, f"{status} ({frequency})")
#             for status, frequency in status_freqs.items()
#         ]
#         self.fields['status'].initial = selected_statuses or []
#
#     status = forms.MultipleChoiceField(
#         label=_("Filter by status"),
#         widget=forms.CheckboxSelectMultiple,
#     )
