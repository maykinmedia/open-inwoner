from rest_framework import serializers

from open_inwoner.accounts.models import User


class UserCustomSerializer(serializers.HyperlinkedModelSerializer):
    age = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "pk",
            "first_name",
            "last_name",
            "age",
            "email",
            "date_joined",
            "birthday",
            "street",
            "housenumber",
            "postcode",
            "city",
        ]

    def get_age(self, obj):
        return obj.get_age()
