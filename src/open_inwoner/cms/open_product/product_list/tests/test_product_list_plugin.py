from unittest.mock import MagicMock, patch

from cms.api import add_plugin, create_page
from cms.test_utils.testcases import CMSTestCase

from open_inwoner.cms.open_product.product_list.models import (
    ProductList as ProductListModel,
)


@patch("open_inwoner.cms.open_product.product_list.cms_plugins.get_open_product_client")
class ProductListTestCase(CMSTestCase):
    def setUp(self):
        self.page = create_page("Product List test Page", "cms/fullwidth.html", "nl")
        self.placeholder = self.page.placeholders.get(slot="content")

        self.product_list = ProductListModel.objects.create(
            title="Mijn reisdocumenten",
            description="Some description",
            theme="Reisdocumenten",
        )

        self.request = MagicMock()
        self.request.user.bsn = "123456789"

        # Mock data
        self.mock_producttypes = {
            "results": [
                {
                    "code": "abc123",
                    "naam": "Paspoort",
                    "acties": [{"naam": "aanvragen"}],
                }
            ]
        }

        self.mock_products = {
            "results": [{"producttype": {"code": "abc123"}, "eind_datum": "2030-12-31"}]
        }

    def render_plugin(self, mock_get_client):
        """
        Helper method. Renders the plugin with mocked data.
        """

        mock_client = MagicMock()
        mock_client.list_product_types.return_value = self.mock_producttypes
        mock_client.list_products.return_value = self.mock_products
        mock_get_client.return_value = mock_client

        plugin_instance = add_plugin(
            self.placeholder,
            "ProductListPlugin",
            "nl",
            title=self.product_list.title,
            description=self.product_list.description,
            theme=self.product_list.theme,
        ).get_plugin_class_instance()

        context = {"request": self.request}
        return plugin_instance.render(context, self.product_list, None)

    def test_context_contains_model_properties(self, mock_get_client):
        context = self.render_plugin(mock_get_client)
        self.assertEqual(context["instance"].title, "Mijn reisdocumenten")
        self.assertEqual(context["instance"].theme, "Reisdocumenten")

    def test_products_are_put_in_context(self, mock_get_client):
        context = self.render_plugin(mock_get_client)
        self.assertIn("products", context)
        self.assertEqual(len(context["products"]), 1)

    def test_producttypes_are_mapped_correctly(self, mock_get_client):
        context = self.render_plugin(mock_get_client)
        product = context["products"][0]
        self.assertEqual(product["producttype"]["code"], "abc123")
        self.assertEqual(product["producttype"]["naam"], "Paspoort")

    def test_product_expiration_flag_is_added(self, mock_get_client):
        context = self.render_plugin(mock_get_client)
        product = context["products"][0]
        self.assertIn("nearing_expiration", product)
        self.assertFalse(product["nearing_expiration"])
