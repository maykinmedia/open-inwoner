from django import forms

from .models import BannerImage, BannerText


class BannerImageForm(forms.ModelForm):
    class Meta:
        model = BannerImage
        fields = ("image", "image_height")

    def clean(self):
        cleaned_data = super().clean()

        image = cleaned_data.get("image")
        image_height = cleaned_data.get("image_height")
        if image and image_height is None:
            cleaned_data["image_height"] = int(image.height)


class BannerTextForm(forms.ModelForm):
    class Meta:
        model = BannerText
        fields = ("title", "description")
