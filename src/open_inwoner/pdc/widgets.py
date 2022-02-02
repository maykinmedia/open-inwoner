from django import forms


class MapWidget(forms.Widget):
    template_name = "admin/widgets/map.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        if value:
            context.update({"lat": value.y, "lng": value.x})

        if hasattr(self, "instance"):
            context["json"] = self.instance.get_geojson_feature()

        return context
