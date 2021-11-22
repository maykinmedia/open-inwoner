from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView

from open_inwoner.search.searches import search_products
from open_inwoner.utils.schema import input_serializer_to_parameters

from .pagination import SearchPagination
from .serializers import SearchQuerySerializer, SearchResponseSerializer


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
        query_serializer.is_valid()
        query_data = query_serializer.data

        # perform search
        search_string = query_data.pop("search", "")
        search_response = search_products(search_string, filters=query_data)

        # paginate
        page = self.paginate_queryset(search_response.hits)
        serializer = self.get_serializer(
            {"results": page, "facets": search_response.facet_groups}
        )
        return self.get_paginated_response(serializer.data)
