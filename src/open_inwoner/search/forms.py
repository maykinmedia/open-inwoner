from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import Feedback


class MultipleChoiceNoValidationField(forms.MultipleChoiceField):
    def valid_value(self, value):
        """used when choices are set up after field validation"""
        return True


class SearchForm(forms.Form):
    query = forms.CharField(
        label=_("Zoek op trefwoord"), max_length=400, required=False
    )
    categories = MultipleChoiceNoValidationField(
        label=_("Categories"), required=False, widget=forms.CheckboxSelectMultiple
    )
    tags = MultipleChoiceNoValidationField(
        label=_("Tags"), required=False, widget=forms.CheckboxSelectMultiple
    )
    organizations = MultipleChoiceNoValidationField(
        label=_("Organizations"), required=False, widget=forms.CheckboxSelectMultiple
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["query"].widget.attrs["placeholder"] = _("Zoeken...")


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ("positive", "remark")
        labels = {"positive": "", "remark": ""}
        help_texts = {"positive": "", "remark": ""}
