from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers


class AutocompleteQuerySerializer(serializers.Serializer):
    search = serializers.CharField(
        required=True, help_text=_("The string for autocomplete")
    )


class AutocompleteResponseSerializer(serializers.Serializer):
    options = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
        help_text=_("List of available options"),
    )
