from rest_framework.viewsets import ModelViewSet

from open_inwoner.accounts.models import Action

from ..serializers import ActionSerializer


class ActionViewSet(ModelViewSet):
    serializer_class = ActionSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        return Action.objects.filter(created_by=self.request.user.id)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
