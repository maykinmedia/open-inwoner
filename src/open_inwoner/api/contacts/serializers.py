from rest_framework import serializers

from ...accounts.models import Contact


class ContactSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Contact
        fields = [
            "uuid",
            "url",
            "first_name",
            "last_name",
            "email",
            "phonenumber",
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
            "url": {"view_name": "api:contacts-detail", "lookup_field": "uuid"},
        }
