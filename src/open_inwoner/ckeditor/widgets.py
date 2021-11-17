from django.forms.widgets import Textarea


class CKEditorWidget(Textarea):
    def __init__(self, attrs=None):
        super().__init__(attrs=attrs)

        self.attrs.setdefault("class", "")
        self.attrs["class"] += " ckeditor-selection"
