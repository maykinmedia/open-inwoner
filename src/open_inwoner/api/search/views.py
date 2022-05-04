from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from open_inwoner.search.searches import search_autocomplete
from open_inwoner.utils.schema import input_serializer_to_parameters

from .serializers import AutocompleteQuerySerializer, AutocompleteResponseSerializer


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
