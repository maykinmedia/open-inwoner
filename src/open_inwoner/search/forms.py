from django import forms
from django.utils.translation import ugettext_lazy as _


class SearchForm(forms.Form):
    query = forms.CharField(label=_("Zoek op trefwoord"), max_length=400, required=True)
