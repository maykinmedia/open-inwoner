from django import forms

from open_inwoner.openzaak.models import ZGWApiGroupConfig


class FetchCasesConfigCheckParams(forms.Form):
    api_group = forms.ModelChoiceField(
        queryset=ZGWApiGroupConfig.objects.all(),
        label="API group",
        help_text="Select the API group to run the check against",
        empty_label=None,
    )
    bsn = forms.CharField(
        label="BSN",
        max_length=9,
        help_text="BSN of the user to fetch cases for",
    )
