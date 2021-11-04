from rest_framework import serializers

from open_inwoner.accounts.models import Appointment


class AppointmentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Appointment
        fields = [
            "uuid",
            "url",
            "name",
            "datetime",
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
            "url": {"view_name": "api:appointments-detail", "lookup_field": "uuid"},
        }
