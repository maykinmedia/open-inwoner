from django import forms


class CompanyBranchChoiceForm(forms.Form):
    branch_number = forms.CharField(widget=forms.HiddenInput())
