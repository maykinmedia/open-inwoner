from django import forms
from django.forms import Form
from django.utils.translation import gettext_lazy as _

from open_inwoner.accounts.models import User
from open_inwoner.openklant.models import ContactFormSubject, OpenKlantConfig
from open_inwoner.utils.validators import validate_phone_number


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
        validators=[validate_phone_number],
        required=False,
    )
    question = forms.CharField(
        label=_("Vraag"),
        max_length=1024,
        widget=forms.Textarea(attrs={"rows": "5"}),
        required=True,
    )

    user: User

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        config = OpenKlantConfig.get_solo()
        self.fields["subject"].queryset = config.contactformsubject_set.order_by(
            "subject"
        )

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
