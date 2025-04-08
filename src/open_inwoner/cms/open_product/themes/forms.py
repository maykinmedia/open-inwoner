from django import forms

from .models import Theme, ThemeList


class ThemeListForm(forms.ModelForm):
    class Meta:
        model = ThemeList
        fields = "__all__"


class ThemeForm(forms.ModelForm):
    class Meta:
        model = Theme
        fields = "__all__"
