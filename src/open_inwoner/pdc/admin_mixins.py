from django import forms

from .widgets import MapWidget


class GeoAdminForm(forms.ModelForm):
    class Meta:
        widgets = {"geometry": MapWidget}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "geometry" in self.fields:
            self.fields["geometry"].widget.instance = self.instance
            self.fields["geometry"].disabled = True


class GeoAdminMixin:
    form = GeoAdminForm

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        # don't show map when creating new location
        if not obj:
            return readonly_fields + ("geometry",)

        return readonly_fields
