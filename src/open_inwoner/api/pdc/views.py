from rest_framework import viewsets
from rest_framework.generics import get_object_or_404

from open_inwoner.pdc.models import Category, Product

from .serializers import (
    CategorySerializer,
    CategoryWithChildSerializer,
    ProductSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = []
    permission_classes = []
    serializer_class = CategoryWithChildSerializer
    lookup_field = "slug"

    def get_object(self):
        """
        Returns the object the view is displaying.

        You may want to override this if you need to provide non-standard
        queryset lookups.  Eg if objects are referenced using multiple
        keyword arguments in the url conf.
        """
        queryset = self.filter_queryset(Category.objects.all())

        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            "Expected view %s to be called with a URL keyword argument "
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            "attribute on the view correctly."
            % (self.__class__.__name__, lookup_url_kwarg)
        )

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def get_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        kwargs.setdefault("context", self.get_serializer_context())
        if "many" in kwargs:
            return CategorySerializer(*args, **kwargs)
        return CategoryWithChildSerializer(*args, **kwargs)

    def get_queryset(self):
        return Category.get_root_nodes()


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = []
    permission_classes = []
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    lookup_field = "slug"
