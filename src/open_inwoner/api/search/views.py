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

    def get(self, request, *args, **kwargs):
        search_string = request.query_params.get("search", "")

        objects = search_products(search_string)
        serializer = self.get_serializer(instance=objects)
        return Response(serializer.data)
