from django import forms
from django.utils.translation import gettext_lazy as _

from eherkenning.validators import KVKValidator


class eHerkenningPasswordLoginForm(forms.Form):
    auth_name = forms.CharField(
        max_length=255,
        required=True,
        label=_("eHerkenning gebruikersnaam"),
        validators=[KVKValidator()],
    )
    auth_pass = forms.CharField(
        max_length=255, required=True, label=_("Wachtwoord"), widget=forms.PasswordInput
    )
    remember_login = forms.CharField(
        label=_("Onthoud mijn eHerkenning gebruikersnaam"), required=False
    )
