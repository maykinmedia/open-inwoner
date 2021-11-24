from rest_framework import serializers

from open_inwoner.api.pdc.serializers import FilerImageSerializer
from open_inwoner.configurations.models import SiteConfiguration


class ConfigDetailSerializer(serializers.ModelSerializer):
    logo = FilerImageSerializer()

    class Meta:
        model = SiteConfiguration
        fields = [
            "name",
            "primary_color",
            "secondary_color",
            "accent_color",
            "logo",
        ]
        read_only_fields = [
            "name",
            "primary_color",
            "secondary_color",
            "accent_color",
            "logo",
        ]
