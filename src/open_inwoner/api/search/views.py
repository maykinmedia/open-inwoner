from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from open_inwoner.search.searches import search_products
from open_inwoner.utils.schema import input_serializer_to_parameters

from .serializers import SearchQuerySerializer, SearchResponseSerializer


class SearchView(APIView):
    permission_classes = []
    authentication_classes = []
    serializer_class = SearchResponseSerializer

    @extend_schema(parameters=input_serializer_to_parameters(SearchQuerySerializer))
    def get(self, request, *args, **kwargs):
        """Search products by query string"""
        # validate query params
        query_serializer = SearchQuerySerializer(data=request.query_params)
        query_serializer.is_valid()
        query_data = query_serializer.data

        # perform search
        search_string = query_data.pop("search", "")
        search_response = search_products(search_string, filters=query_data)
        serializer = self.serializer_class(instance=search_response)
        return Response(serializer.data)
