from django import forms
from django.urls import reverse


class PrivateFileWidget(forms.ClearableFileInput):
    template_name = "utils/widgets/private_file_input.html"

    def __init__(self, *args, **kwargs):
        self.url_name = kwargs.pop("url_name")
        super().__init__(*args, **kwargs)

    def get_context(self, name, value, attrs):
        """
        Return value-related substitutions.
        """
        context = super().get_context(name, value, attrs)
        if self.is_initial(value):
            context["url"] = reverse(
                self.url_name, kwargs={"uuid": value.instance.uuid}
            )
        return context
