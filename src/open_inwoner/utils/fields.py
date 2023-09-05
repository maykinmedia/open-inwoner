from django.db import models
from django.forms import Textarea


class CSSEditorWidget(Textarea):
    def __init__(self, attrs=None):
        super().__init__(attrs=attrs)

        self.attrs.setdefault("class", "")
        self.attrs["cols"] = "90"
        self.attrs["class"] += " textfield--code textfield--code--css"


class CSSField(models.TextField):
    # dummy for readability and overrides
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
