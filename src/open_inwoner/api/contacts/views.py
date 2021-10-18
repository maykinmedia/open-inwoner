from rest_framework.viewsets import ModelViewSet

from ...accounts.models import Contact
from .serializers import ContactSerializer


class ContactViewSet(ModelViewSet):
    serializer_class = ContactSerializer
    lookup_field = "reference"

    def get_queryset(self):
        return Contact.objects.filter(created_by=self.request.user.id)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
