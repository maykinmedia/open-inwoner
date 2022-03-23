from django import forms

from .choices import YesNo


class ProductFinderForm(forms.Form):
    answer = forms.CharField(widget=forms.RadioSelect(choices=YesNo.choices))
