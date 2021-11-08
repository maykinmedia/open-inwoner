from django.utils.translation import ugettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from open_inwoner.search.searches import search_products

from .serializers import ProductDocumentSerializer


class SearchView(APIView):
    permission_classes = []
    authentication_classes = []
    serializer_class = ProductDocumentSerializer

    def get_serializer(self, **kwargs):
        return self.serializer_class(
            many=True,
            context={"request": self.request, "view": self},
            **kwargs,
        )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="search",
                required=False,
                type=OpenApiTypes.STR,
                description=_(
                    "The search string. If empty the empty list is returned."
                ),
                location=OpenApiParameter.QUERY,
            )
        ],
    )
    def get(self, request, *args, **kwargs):
        """Search products by query string"""
        search_string = request.query_params.get("search", "")

        objects = search_products(search_string)
        serializer = self.get_serializer(instance=objects)
        return Response(serializer.data)
