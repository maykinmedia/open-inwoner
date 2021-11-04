from rest_framework import serializers

from open_inwoner.accounts.models import Action


class ActionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Action
        fields = [
            "uuid",
            "url",
            "name",
            "created_on",
            "updated_on",
        ]
        read_only_fields = [
            "uuid",
            "url",
            "created_on",
            "updated_on",
        ]
        extra_kwargs = {
            "url": {"view_name": "api:actions-detail", "lookup_field": "uuid"},
        }
