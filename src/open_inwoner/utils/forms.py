from django import forms
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.template.defaultfilters import filesizeformat
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _


class PrivateFileWidget(forms.ClearableFileInput):
    template_name = "utils/widgets/private_file_input.html"

    def __init__(self, *args, **kwargs):
        self.url_name = kwargs.pop("url_name")
        super().__init__(*args, **kwargs)
        self.attrs.update({"accept": settings.UPLOAD_FILE_TYPES})

    def get_context(self, name, value, attrs):
        """
        Return value-related substitutions.
        """
        context = super().get_context(name, value, attrs)
        if self.is_initial(value):
            context["url"] = reverse(
                self.url_name, kwargs={"uuid": value.instance.uuid}
            )
        return context


class LimitedUploadFileField(forms.FileField):
    upload_error_messages = {
        "min_size": _(
            "Een aangeleverd bestand dient minimaal %(size)s te zijn, uw bestand is te klein."
        ),
        "max_size": _(
            "Een aangeleverd bestand dient maximaal %(size)s te zijn, uw bestand is te groot."
        ),
        "file_type": _(
            "Het type bestand dat u hebt geüpload is ongeldig. Geldige bestandstypen zijn: pdf, docx, doc, xlsx, xls, jpeg, jpg, png, txt, odt, odf, ods"
        ),
    }

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        attrs.update({"accept": settings.UPLOAD_FILE_TYPES})
        return attrs

    def clean(self, *args, **kwargs):
        f = super().clean(*args, **kwargs)

        if isinstance(f, InMemoryUploadedFile) or isinstance(f, TemporaryUploadedFile):
            _error_messages = self.upload_error_messages
            min_upload_size = settings.MIN_UPLOAD_SIZE
            max_upload_size = settings.MAX_UPLOAD_SIZE
            file_types = settings.UPLOAD_FILE_TYPES

            # checking file size limits
            if f.size < min_upload_size:
                raise forms.ValidationError(
                    _error_messages["min_size"],
                    params={"size": filesizeformat(min_upload_size)},
                )
            if f.size > max_upload_size:
                raise forms.ValidationError(
                    _error_messages["max_size"],
                    params={"size": filesizeformat(max_upload_size)},
                )
            # checking file type limits
            if f.content_type not in file_types.split(","):
                raise forms.ValidationError(_error_messages["file_type"])

        return f
