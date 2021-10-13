from django import forms
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from django_registration.forms import RegistrationForm

from .models import User


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
