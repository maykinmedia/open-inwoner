from import_export import resources

from .models import Category, Product


class CategoryResource(resources.ModelResource):
    class Meta:
        model = Category
        import_id_fields = ("slug",)


class ProductResource(resources.ModelResource):
    class Meta:
        model = Product
        import_id_fields = ("slug",)
