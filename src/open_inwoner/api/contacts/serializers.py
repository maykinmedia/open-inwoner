from rest_framework import serializers

from ...accounts.models import Contact


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = [
            "reference",
            "first_name",
            "last_name",
            "email",
            "phonenumber",
            "created_on",
            "updated_on",
        ]
        read_only_fields = ("reference",)
