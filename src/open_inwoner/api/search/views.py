from django.utils.translation import ugettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from open_inwoner.search.searches import search_products

from .serializers import SearchResponseSerializer


class SearchView(APIView):
    permission_classes = []
    authentication_classes = []
    serializer_class = SearchResponseSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="search",
                required=False,
                type=OpenApiTypes.STR,
                description=_(
                    "The search string. If empty all the documents are returned."
                ),
                location=OpenApiParameter.QUERY,
            )
        ],
    )
    def get(self, request, *args, **kwargs):
        """Search products by query string"""
        search_string = request.query_params.get("search", "")

        search_response = search_products(search_string)
        serializer = self.serializer_class(instance=search_response)
        return Response(serializer.data)
