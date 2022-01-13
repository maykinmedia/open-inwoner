from django import forms
from django.utils.translation import ugettext_lazy as _

from django_registration.forms import RegistrationForm

from .models import Action, Contact, Document, Message, User


class CustomRegistrationForm(RegistrationForm):
    first_name = forms.CharField(label=_("First name"), max_length=255, required=True)
    last_name = forms.CharField(label=_("Last name"), max_length=255, required=True)

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
        )


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "birthday",
            "street",
            "housenumber",
            "postcode",
            "city",
        )


class ThemesForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("selected_themes",)
        widgets = {"selected_themes": forms.widgets.CheckboxSelectMultiple}


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ("first_name", "last_name", "email", "phonenumber")

    def save(self, user, commit=True):
        self.instance.created_by = user
        return super().save(commit=commit)


class ActionForm(forms.ModelForm):
    class Meta:
        model = Action
        fields = ("name", "status", "end_date")

    def save(self, user, commit=True):
        self.instance.created_by = user
        return super().save(commit=commit)


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ("name", "file")

    def save(self, user, commit=True):
        self.instance.owner = user
        return super().save(commit=commit)


class InboxForm(forms.ModelForm):
    content = forms.CharField(label="", widget=forms.Textarea)
    receiver = forms.ModelChoiceField(
        queryset=User.objects.all(),
        to_field_name="email",
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = Message
        fields = ("content", "receiver")

    def save(self, sender=None, commit=True):
        self.instance.sender = sender

        return super().save(commit)


class InboxStartForm(forms.ModelForm):
    receiver = forms.ModelChoiceField(
        label=_("Contactpersoon"), queryset=User.objects.all(), to_field_name="email"
    )
    content = forms.CharField(
        label="",
        widget=forms.Textarea(attrs={"placeholder": _("Schrijf een bericht...")}),
    )

    class Meta:
        model = Message
        fields = ("receiver", "content")

    def __init__(self, user, **kwargs):
        self.user = user

        super().__init__(**kwargs)

        active_contacts = self.user.get_active_contacts()
        choices = [[c.email, f"{c.first_name} {c.last_name}"] for c in active_contacts]
        self.fields["receiver"].choices = choices

    def save(self, commit=True):
        self.instance.sender = self.user

        return super().save(commit)
