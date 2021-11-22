from datetime import date

from django.utils.translation import ugettext_lazy as _

from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import UpdateModelMixin
from rest_framework.response import Response

from open_inwoner.api.serializers import DetailSerializer


class DeactivateUserView(UpdateModelMixin, GenericAPIView):
    @extend_schema(
        operation_id="auth_user_deactivate",
        responses={200: DetailSerializer, 403: DetailSerializer},
    )
    def post(self, request, *args, **kwargs):
        """
        Updates UserModel concerning deactivation.
        Fields which are updated: is_active, deactivated_on.
        """
        user = self.request.user
        if user.is_staff:
            return Response(
                {"detail": _("Your account cannot be deactivated.")}, status=403
            )

        user.is_active = False
        user.deactivated_on = date.today()
        user.save()
        return Response({"detail": _("Your account has been deactivated.")}, status=200)
