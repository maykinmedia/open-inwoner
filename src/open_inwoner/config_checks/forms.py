from django import forms

from open_inwoner.accounts.models import User
from open_inwoner.openzaak.models import ZGWApiGroupConfig


class FetchCasesConfigCheckParams(forms.Form):
    api_group = forms.ModelChoiceField(
        queryset=ZGWApiGroupConfig.objects.all(),
        required=False,
        help_text="API group to fetch data for",
    )
    bsn = forms.CharField(
        label="BSN",
        max_length=9,
        help_text="BSN of the user to fetch cases for",
    )


class FetchBRPConfigCheckParams(forms.Form):
    bsn = forms.CharField(
        label="BSN",
        max_length=9,
        help_text="BSN to fetch BRP data for",
    )


class FetchUserfeedConfigCheckParams(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        help_text="User to fetch data for",
    )
