from datetime import date

from rest_framework.generics import UpdateAPIView
from rest_framework.response import Response

from open_inwoner.accounts.models import User


class DeactivateUserView(UpdateAPIView):
    def put(self, request, *args, **kwargs):
        return Response({"detail": 'Methode "PUT" not allowed.'}, status=405)

    def patch(self, request, *args, **kwargs):
        user = User.objects.get(id=self.request.user.id)
        if user.is_staff:
            return Response({"detail": "Staff user cannot be deactivated."}, status=403)

        user.is_active = False
        user.deactivated_on = date.today()
        user.save()
        return Response({"detail": "User has been deactivated."}, status=200)
