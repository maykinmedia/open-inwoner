from rest_framework.viewsets import ModelViewSet

from open_inwoner.accounts.models import Document

from ..serializers import DocumentSerializer


class DocumentViewSet(ModelViewSet):
    serializer_class = DocumentSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        return Document.objects.filter(owner=self.request.user.id)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
