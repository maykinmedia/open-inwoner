from django import forms
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from django_registration.forms import RegistrationForm

from .models import User


class CustomRegistrationForm(RegistrationForm):
    """
    Form for registering a new user account.

    Validates that the requested email is not already in use, and
    requires the password to be entered twice to catch typos.

    Subclasses should feel free to add any additional validation they
    need, but should avoid defining a ``save()`` method -- the actual
    saving of collected user data is delegated to the active
    registration backend.

    """

    required_css_class = "required"
    first_name = forms.CharField(label=_("First name"), max_length=255, required=True)
    last_name = forms.CharField(label=_("Last name"), max_length=255, required=True)
    error_messages = {
        "password_mismatch": _("The two password fields didn’t match."),
    }

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
        )
