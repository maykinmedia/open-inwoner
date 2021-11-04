from rest_framework import serializers

from open_inwoner.accounts.models import Document


class DocumentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Document
        fields = [
            "uuid",
            "url",
            "name",
            "file",
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
            "url": {"view_name": "api:documents-detail", "lookup_field": "uuid"},
        }
