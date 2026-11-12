from django import forms
from django.utils.translation import gettext_lazy as _


class GespreksbijdrageForm(forms.Form):
    tekst = forms.CharField(
        label=_("Schrijf uw bericht"),
        widget=forms.Textarea(attrs={"rows": 2}),
        max_length=5000,
    )
    bijlage = forms.FileField(label=_("Bijlage"), required=False)


class GesprekStartForm(GespreksbijdrageForm):
    onderwerp = forms.CharField(label=_("Onderwerp"), max_length=200)
