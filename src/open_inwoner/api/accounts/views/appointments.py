from rest_framework.viewsets import ModelViewSet

from open_inwoner.accounts.models import Appointment

from ..serializers import AppointmentSerializer


class AppointmentViewSet(ModelViewSet):
    serializer_class = AppointmentSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        return Appointment.objects.filter(created_by=self.request.user.id)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
