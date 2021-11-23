from django.utils.translation import ugettext_lazy as _

from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from open_inwoner.configurations.models import SiteConfiguration

from .serializers import ConfigDetailSerializer


class SiteConfigurationView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(responses={200: ConfigDetailSerializer})
    def get(self, request, format=None):
        config = SiteConfiguration.get_solo()
        serializer = ConfigDetailSerializer(config)
        return Response(serializer.data)
