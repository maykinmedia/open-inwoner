from django import forms

from .models import Banner


class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = ("title", "image", "image_height")

    def clean(self):
        cleaned_data = super().clean()

        image = cleaned_data.get("image")
        image_height = cleaned_data.get("image_height")
        if image and image_height is None:
            cleaned_data["image_height"] = int(image.height)
