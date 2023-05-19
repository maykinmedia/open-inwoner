from django import forms
from django.forms import Form
from django.utils.translation import gettext_lazy as _

from open_inwoner.openklant.models import ContactFormSubject, OpenKlantConfig
from open_inwoner.utils.validators import validate_phone_number


class ContactForm(Form):
    subject = forms.ModelChoiceField(
        label=_("Onderwerp"),
        required=True,
        queryset=ContactFormSubject.objects.none(),
    )
    name = forms.CharField(
        label=_("Naam"),
        max_length=64,
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        config = OpenKlantConfig.get_solo()
        self.fields["subject"].queryset = config.contactformsubject_set.order_by(
            "subject"
        )

    def clean(self, *args, **kwargs):
        cleaned_data = super().clean(*args, **kwargs)

        email = cleaned_data["email"]
        phonenumber = cleaned_data["phonenumber"]

        if not email and not phonenumber:
            msg = _("Vul een e-mailadres of telefoonnummer in.")
            self.add_error("email", msg)
            self.add_error("phonenumber", msg)
