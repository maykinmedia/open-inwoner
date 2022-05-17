from django.utils.translation import ugettext_lazy as _

from django_webtest import WebTest

from ..admin import ProductAdminForm
from .factories import CategoryFactory


class TestProductFormValidation(WebTest):
    def test_form_is_valid_without_data_provided(self):
        form = ProductAdminForm()
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {})

    def test_form_when_required_fields_are_missing(self):
        data = {}
        form = ProductAdminForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {
                "name": [_("Dit veld is vereist.")],
                "slug": [_("Dit veld is vereist.")],
                "content": [_("Dit veld is vereist.")],
                "categories": [_("Dit veld is vereist.")],
                "costs": [_("Dit veld is vereist.")],
            },
        )

    def test_form_is_valid_with_proper_data(self):
        category = CategoryFactory()
        data = {
            "name": "a name",
            "slug": "a-name",
            "content": "some content",
            "costs": 0.0,
            "categories": [category.id],
        }
        form = ProductAdminForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.errors, {})

    def test_form_fails_when_both_link_and_snippet_are_provided(self):
        category = CategoryFactory()
        data = {
            "name": "a name",
            "slug": "a-name",
            "content": "some content",
            "costs": 0.0,
            "categories": [category.id],
            "link": "https://test.com",
            "form_snippet": "<div>code snippet</div>",
        }
        form = ProductAdminForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {
                "__all__": [
                    _(
                        "Either link or form snippet should be provided. You can not fill in both."
                    )
                ]
            },
        )

    def test_form_is_valid_when_only_link_is_provided(self):
        category = CategoryFactory()
        data = {
            "name": "a name",
            "slug": "a-name",
            "content": "some content",
            "costs": 0.0,
            "categories": [category.id],
            "link": "https://test.com",
        }
        form = ProductAdminForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.errors, {})

    def test_form_is_valid_when_only_snippet_is_provided(self):
        category = CategoryFactory()
        data = {
            "name": "a name",
            "slug": "a-name",
            "content": "some content",
            "costs": 0.0,
            "categories": [category.id],
            "form_snippet": "<div>code snippet</div>",
        }
        form = ProductAdminForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.errors, {})
