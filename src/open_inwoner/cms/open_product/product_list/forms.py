from django import forms

from .models import ProductList
from .utils import get_open_product_client


def get_formatted_themes():
    try:
        client = get_open_product_client()
        themes = client.list_themes()["results"]
        return [(theme["uuid"], theme["naam"]) for theme in themes]
    except Exception:
        return ["No themes available before Open Product initialization."]


class ProductListForm(forms.ModelForm):
    class Meta:
        model = ProductList
        fields = "__all__"
        widgets = {
            "theme": forms.Select(choices=get_formatted_themes()),
        }

    # Necessary to (re)load the themes without server restarts
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["theme"].widget = forms.Select(choices=get_formatted_themes())
