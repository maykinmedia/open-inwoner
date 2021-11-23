from rest_framework import fields, serializers

from open_inwoner.configurations.models import SiteConfiguration


class ConfigDetailSerializer(serializers.ModelSerializer):
    logo = serializers.URLField(source="logo.url")

    class Meta:
        model = SiteConfiguration
        fields = [
            "name",
            "primary_color",
            "secondary_color",
            "accent_color",
            "logo",
        ]
