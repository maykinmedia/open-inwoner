import random

from django import forms
from django.forms import Form
from django.utils.translation import gettext_lazy as _

from simplemathcaptcha.fields import MathCaptchaField

from open_inwoner.accounts.models import User
from open_inwoner.openklant.models import ContactFormSubject, OpenKlantConfig
from open_inwoner.utils.validators import DutchPhoneNumberValidator


def _get_random_numbers():
    # Generate two random numbers for the question
    return random.randint(0, 10), random.randint(0, 10)  # Adjust the range as needed


class CustomMathCaptchaField(MathCaptchaField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.num1, self.num2 = _get_random_numbers()
        self.answer = self.num1 + self.num2
        self.question = _("Woettt is {} + {}?").format(self.num1, self.num2)
        print(f"Captcha question: {self.question}")  # Debugging
        print(f'Translation check: {_("Controleer je berekening test.")}')

    def clean(self, value):
        # Ensure to call the parent clean method
        value = super().clean(value)
        if value != self.answer:
            raise forms.ValidationError(
                _("Controleer je berekening en probeer het opnieuw.")
            )
        return value


class ContactForm(Form):
    subject = forms.ModelChoiceField(
        label=_("Onderwerp"),
        required=True,
        queryset=ContactFormSubject.objects.none(),
        empty_label=_("Selecteren"),
    )
    first_name = forms.CharField(
        label=_("Voornaam"),
        max_length=255,
        required=True,
    )
    infix = forms.CharField(
        label=_("Tussenvoegsel"),
        max_length=64,
        required=False,
    )
    last_name = forms.CharField(
        label=_("Achternaam"),
        max_length=255,
        required=True,
    )
    email = forms.EmailField(
        label=_("E-mailadres"),
        required=False,
    )
    phonenumber = forms.CharField(
        label=_("Telefoonnummer"),
        max_length=15,
        validators=[DutchPhoneNumberValidator()],
        required=False,
    )
    question = forms.CharField(
        label=_("Vraag"),
        max_length=1024,
        widget=forms.Textarea(attrs={"rows": "5"}),
        required=True,
    )
    captcha = CustomMathCaptchaField(
        label=_("Beantwoord deze rekensom"),
        error_messages={
            "invalid": _("Controleer je berekening en probeer het opnieuw.")
        },
    )

    user: User

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        config = OpenKlantConfig.get_solo()
        self.fields["subject"].queryset = config.contactformsubject_set.all()

        if self.user.is_authenticated:
            del self.fields["first_name"]
            del self.fields["last_name"]
            del self.fields["infix"]
            if self.user.email:
                del self.fields["email"]
            if self.user.phonenumber:
                del self.fields["phonenumber"]

    def clean(self, *args, **kwargs):
        cleaned_data = super().clean(*args, **kwargs)

        email = cleaned_data.get("email", "")
        phonenumber = cleaned_data.get("phonenumber", "")

        if ("email" in self.fields and not email) and (
            "phonenumber" in self.fields and not phonenumber
        ):
            msg = _("Vul een e-mailadres of telefoonnummer in.")
            self.add_error("email", msg)
            self.add_error("phonenumber", msg)

        if self.user.is_authenticated:
            if not email and self.user.email:
                cleaned_data["email"] = self.user.email
            if not phonenumber and self.user.phonenumber:
                cleaned_data["phonenumber"] = self.user.phonenumber

            cleaned_data["first_name"] = self.user.first_name
            cleaned_data["infix"] = self.user.infix
            cleaned_data["last_name"] = self.user.last_name

        return cleaned_data
