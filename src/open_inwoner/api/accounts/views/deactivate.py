from datetime import date

from rest_framework.generics import UpdateAPIView
from rest_framework.response import Response

from open_inwoner.accounts.models import User


class DeactivateUserView(UpdateAPIView):
    def patch(self, request, *args, **kwargs):
        user = User.objects.get(id=self.request.user.id)
        user.is_active = False
        user.deactivated_on = date.today()
        user.save()
        return Response({"detail": "user has been deactivated"}, status=200)
