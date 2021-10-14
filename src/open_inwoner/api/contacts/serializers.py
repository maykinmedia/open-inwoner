from rest_framework import serializers

from ...accounts.models import Contact


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = [
            "first_name",
            "last_name",
            "email",
            "phonenumber",
            "created_on",
            "updated_on",
        ]
