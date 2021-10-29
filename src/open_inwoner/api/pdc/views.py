from rest_framework import viewsets

from open_inwoner.pdc.models import Category, Product

from .serializers import CategorySerializer, ProductSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = []
    permission_classes = []
    serializer_class = CategorySerializer
    lookup_field = "slug"

    def get_queryset(self):
        return Category.get_root_nodes()


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = []
    permission_classes = []
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    lookup_field = "slug"
