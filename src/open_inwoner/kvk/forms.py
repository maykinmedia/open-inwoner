from django import forms
from django.utils.translation import gettext as _


class CompanyBranchChoiceForm(forms.Form):
    branch_number = forms.CharField(widget=forms.HiddenInput(), required=False)

    def __init__(self, company_branches, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.company_branches = company_branches

    def clean_branch_number(self):
        form_data = self.cleaned_data.get("branch_number")

        if not any(
            form_data == branch.get("vestigingsnummer")
            for branch in self.company_branches
        ):
            raise forms.ValidationError(
                _("Invalid branch number for the current KvK number")
            )

        return self.cleaned_data
