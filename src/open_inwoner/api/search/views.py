from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from open_inwoner.search.results import ProductSearchResult
from open_inwoner.search.searches import search_autocomplete, search_products
from open_inwoner.utils.schema import input_serializer_to_parameters

from .pagination import SearchPagination
from .serializers import (
    AutocompleteQuerySerializer,
    AutocompleteResponseSerializer,
    SearchQuerySerializer,
    SearchResponseSerializer,
)


class SearchView(GenericAPIView):
    permission_classes = []
    authentication_classes = []
    serializer_class = SearchResponseSerializer
    pagination_class = SearchPagination
    action = "list"  # for spectacular

    @extend_schema(parameters=input_serializer_to_parameters(SearchQuerySerializer))
    def get(self, request, *args, **kwargs):
        """Search products by query string"""
        # validate query params
        query_serializer = SearchQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        query_data = query_serializer.data

        # perform search
        search_string = query_data.pop("search", "")
        search_response = search_products(search_string, filters=query_data)
        # paginate
        page = self.paginate_queryset(search_response.results)
        serializer = self.get_serializer(
            ProductSearchResult(results=page, facets=search_response.facets)
        )
        return self.get_paginated_response(serializer.data)


class AutocompleteView(APIView):
    permission_classes = []
    authentication_classes = []
    serializer_class = AutocompleteResponseSerializer

    @extend_schema(
        parameters=input_serializer_to_parameters(AutocompleteQuerySerializer)
    )
    def get(self, request, *args, **kwargs):
        # validate query params
        query_serializer = AutocompleteQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        # perform search
        search_string = query_serializer.data["search"]
        search_response = search_autocomplete(search_string)
        serializer = self.serializer_class(search_response)
        return Response(serializer.data)
