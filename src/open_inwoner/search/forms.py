from django import forms
from django.forms import widgets
from django.forms.widgets import Textarea
from django.utils.translation import ugettext_lazy as _

from open_inwoner.components.templatetags.form_tags import form

from .models import Feedback


class MultipleChoiceNoValidationField(forms.MultipleChoiceField):
    def valid_value(self, value):
        """used when choices are set up after field validation"""
        return True


class SearchForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["query"].widget.attrs["placeholder"] = _("Zoeken...")

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


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ("positive", "remark")
        labels = {"positive": "", "remark": ""}
        help_texts = {"positive": "", "remark": ""}
