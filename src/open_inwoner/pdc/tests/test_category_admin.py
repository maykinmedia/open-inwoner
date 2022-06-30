from django.urls import reverse

from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import UserFactory

from ..models.category import Category
from .factories import CategoryFactory


class TestAdminCategoryForm(WebTest):
    def setUp(self):
        self.user = UserFactory(is_superuser=True, is_staff=True)

    def test_user_can_publish_root_category_on_add_form(self):
        form = self.app.get(reverse("admin:pdc_category_add"), user=self.user).forms[
            "category_form"
        ]
        form["name"] = "foo1"
        form["slug"] = "foo1"
        form["_position"] = "sorted-child"
        form["_ref_node_id"] = ""
        form.submit()
        category = Category.objects.first()
        self.assertEqual(category.slug, "foo1")
        self.assertTrue(category.published)

    def test_user_can_publish_child_category_with_root_published_on_add_form(self):
        root = CategoryFactory(path="0002", slug="foo2")
        form = self.app.get(reverse("admin:pdc_category_add"), user=self.user).forms[
            "category_form"
        ]
        form["name"] = "bar1"
        form["slug"] = "bar1"
        form["_position"] = "sorted-child"
        form["_ref_node_id"] = root.id
        form.submit()
        updated_category = Category.objects.get(slug="bar1")
        self.assertTrue(updated_category.published)

    def test_user_cannot_publish_child_category_without_root_published_on_add_form(
        self,
    ):
        category = CategoryFactory(path="0003", slug="foo3", published=False)
        form = self.app.get(reverse("admin:pdc_category_add"), user=self.user).forms[
            "category_form"
        ]

        form["name"] = "bar2"
        form["slug"] = "bar2"
        form["_position"] = "sorted-child"
        form["_ref_node_id"] = category.id
        form.submit()
        categories = Category.objects.filter(slug="bar2")
        self.assertEqual(categories.count(), 0)

    def test_user_can_publish_root_category_on_list_page(self):
        CategoryFactory(path="0004", slug="foo4", published=False)
        form = self.app.get(
            reverse("admin:pdc_category_changelist"), user=self.user
        ).forms["changelist-form"]
        form["form-0-published"] = True
        form.submit("_save")
        updated_category = Category.objects.get(slug="foo4")
        self.assertTrue(updated_category.published)

    def test_user_can_publish_child_category_with_root_published_on_list_page(self):
        root = CategoryFactory(path="0005", slug="foo5")
        root.add_child(path="00050001", slug="bar3", published=False)
        form = self.app.get(
            reverse("admin:pdc_category_changelist"), user=self.user
        ).forms["changelist-form"]
        form["form-1-published"] = True
        form.submit("_save")
        updated_category = Category.objects.get(slug="bar3")
        self.assertTrue(updated_category.published)

    def test_user_cannot_publish_child_category_without_root_published_on_list_page(
        self,
    ):
        root = CategoryFactory(path="0006", slug="foo6", published=False)
        root.add_child(path="00060001", slug="bar4", published=False)
        form = self.app.get(
            reverse("admin:pdc_category_changelist"), user=self.user
        ).forms["changelist-form"]
        form["form-1-published"] = True
        form.submit("_save")
        updated_category = Category.objects.get(slug="bar4")
        self.assertFalse(updated_category.published)
