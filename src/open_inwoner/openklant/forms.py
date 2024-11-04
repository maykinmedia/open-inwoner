from django import forms
from django.utils.translation import gettext_lazy as _

from open_inwoner.accounts.models import User
from open_inwoner.openklant.models import ContactFormSubject, OpenKlantConfig
from open_inwoner.openklant.views.utils import generate_question_answer_pair
from open_inwoner.utils.validators import DutchPhoneNumberValidator


class ContactForm(forms.Form):
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
    captcha = forms.IntegerField(
        label=_("Beantwoord deze rekensom"),
        required=True,
    )

    user: User

    def __init__(self, user, request_session, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.request_session = request_session

        config = OpenKlantConfig.get_solo()
        self.fields["subject"].queryset = config.contactformsubject_set.all()

        if self.user.is_authenticated:
            del self.fields["first_name"]
            del self.fields["last_name"]
            del self.fields["infix"]
            del self.fields["captcha"]
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
        else:
            # captcha for anon users
            captcha_answer = cleaned_data.get("captcha")
            if (
                captcha_answer
                and not captcha_answer == self.request_session["captcha_answer"]
            ):
                self.add_error("captcha", _("Fout antwoord, probeer het opnieuw."))

            captcha_question, captcha_answer = generate_question_answer_pair()

            self.request_session["captcha_question"] = captcha_question
            self.request_session["captcha_answer"] = captcha_answer

        return cleaned_data
