import mimetypes
import secrets

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.template.defaultfilters import filesizeformat
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class ErrorMessageMixin:
    default_error_messages = {
        "required": _(
            "Het verplichte veld {field_name} is niet (goed) ingevuld. Vul het veld in."
        )
    }

    def __init__(self, *args, **kwargs):
        custom_error_messages = {}
        if "custom_error_messages" in kwargs:
            custom_error_messages = kwargs.pop("custom_error_messages")

        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():

            field_error_messages = custom_error_messages.get(field_name, {})

            error_messages = {}
            for key in self.default_error_messages.keys():
                if key in field_error_messages.keys():
                    error_message = field_error_messages[key].format(
                        field_name=f'"{field.label}"'
                    )
                else:
                    error_message = self.default_error_messages[key].format(
                        field_name=f'"{field.label}"'
                    )
                error_messages[key] = error_message

            field.error_messages.update({**error_messages})


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


class LimitedUploadFileField(forms.FileField):
    upload_error_messages = {
        "min_size": _(
            "Een aangeleverd bestand dient minimaal %(size)s te zijn, uw bestand is te klein."
        ),
        "max_size": _(
            "Een aangeleverd bestand dient maximaal %(size)s te zijn, uw bestand is te groot."
        ),
        "file_type": _(
            "Het type bestand dat u hebt geüpload is ongeldig. Geldige bestandstypen zijn: %(file_extensions)s"
        ),
    }

    def __init__(
        self,
        *args,
        min_upload_size: int | None = None,
        max_upload_size: int | None = None,
        allowed_mime_types: list[str] | None = None,
        **kwargs,
    ):
        self._min_upload_size = min_upload_size
        self._max_upload_size = max_upload_size
        self._allowed_mime_types = allowed_mime_types or []

        for mt in self._allowed_mime_types:
            if not mimetypes.guess_extension(mt):
                raise ValueError(f"Cannot guess extension for mimetype {mt}")

        super().__init__(*args, **kwargs)

    @property
    def min_upload_size(self):
        return self._min_upload_size or settings.MIN_UPLOAD_SIZE

    @property
    def max_upload_size(self):
        return self._max_upload_size or settings.MAX_UPLOAD_SIZE

    @property
    def allowed_mime_types(self):
        return (
            ",".join(self._allowed_mime_types)
            if self._allowed_mime_types
            else settings.UPLOAD_FILE_TYPES
        )

    @property
    def allowed_extensions(self):
        return [
            mimetypes.guess_extension(mt)[1:]
            for mt in self.allowed_mime_types.split(",")
        ]

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        attrs.update({"accept": self.allowed_mime_types})
        return attrs

    def clean(self, *args, **kwargs):
        f = super().clean(*args, **kwargs)

        if isinstance(f, InMemoryUploadedFile) or isinstance(f, TemporaryUploadedFile):
            _error_messages = self.upload_error_messages

            # checking file size limits
            if f.size < self.min_upload_size:
                raise forms.ValidationError(
                    _error_messages["min_size"],
                    params={"size": filesizeformat(self.min_upload_size)},
                )
            if f.size > self.max_upload_size:
                raise forms.ValidationError(
                    _error_messages["max_size"],
                    params={"size": filesizeformat(self.max_upload_size)},
                )
            # checking file type limits
            if f.content_type not in self.allowed_mime_types.split(","):
                raise forms.ValidationError(
                    _error_messages["file_type"]
                    % {"file_extensions": ", ".join(self.allowed_extensions)}
                )

        return f


class MathCaptchaField(forms.Field):
    def __init__(
        self,
        range_: tuple = (1, 10),
        operators: list[str] | None = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.widget = forms.TextInput()
        self.range_ = range_
        self.operators = operators or ["+", "-"]
        self.question, self.answer = self.generate_question_answer_pair(
            self.range_, self.operators
        )

    @staticmethod
    def generate_question_answer_pair(
        range_: tuple[int, int],
        operators: list[str],
    ) -> tuple[str, int]:
        lower, upper = range_
        num1 = secrets.choice(range(lower, upper))
        num2 = secrets.choice(range(lower, upper))
        operator = secrets.choice(operators)

        # exclude negative results
        num1, num2 = max(num1, num2), min(num1, num2)

        question = _("What is {num1} {operator_str} {num2}?").format(
            num1=num1, operator_str=operator, num2=num2
        )

        match operator:
            case "+":
                answer = num1 + num2
            case "-":
                answer = num1 - num2

        return question, answer

    def clean(self, value: str) -> str:
        if not value:
            raise forms.ValidationError(_("Dit veld is vereist."))
        if not isinstance(value, str):
            raise forms.ValidationError(_("Voer een geheel getal in."))
        if value.isspace():
            raise forms.ValidationError(_("Voer een geheel getal in."))
        if int(value) != self.answer:
            raise forms.ValidationError(_("Fout antwoord, probeer het opnieuw."))
        return value
