from django import forms
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from django_registration.forms import RegistrationForm

from .models import Action, Contact, Document, User


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
