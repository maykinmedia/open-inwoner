from django import forms


class FetchCasesConfigCheckParams(forms.Form):
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
    pass
