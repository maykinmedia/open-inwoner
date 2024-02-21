from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils.translation import gettext as _

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from open_inwoner.accounts.tests.factories import GroupFactory, UserFactory
from open_inwoner.openzaak.tests.factories import ZaakTypeConfigFactory

from ..models.category import Category
from .factories import CategoryFactory


@disable_admin_mfa()
class TestAdminCategoryForm(WebTest):
    def setUp(self):
        self.user = UserFactory(is_superuser=True, is_staff=True)

    def test_user_can_publish_root_category_on_add_form(self):
        form = self.app.get(reverse("admin:pdc_category_add"), user=self.user).forms[
            "category_form"
        ]
        form["name"] = "foo1"
        form["slug"] = "foo1"
        form["published"] = True
        form["_position"] = "first-child"
        form["_ref_node_id"] = 0
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
        form["published"] = True
        form["_position"] = "first-child"
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
        form["published"] = True
        form["_position"] = "first-child"
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

    def test_access_limited_to_linked_auth_groups(self):
        super_user = UserFactory(is_superuser=True, is_staff=True)

        group = GroupFactory()
        group_user = UserFactory(is_staff=True)
        group_user.user_permissions.add(
            Permission.objects.get(codename="view_category"),
        )
        group_user.groups.add(group)

        category_general = CategoryFactory(
            path="everyone", name="everyone", published=True
        )
        category_grouped = CategoryFactory(
            path="grouped", name="grouped", published=True
        )
        category_grouped.access_groups.add(group)

        with self.subTest("superuser sees all in list"):
            response = self.app.get(
                reverse("admin:pdc_category_changelist"), user=super_user
            )
            categories = list(response.context["cl"].queryset.all())
            # list shows all categories
            self.assertEqual(categories, [category_general, category_grouped])

        with self.subTest("user list is limited by group"):
            response = self.app.get(
                reverse("admin:pdc_category_changelist"), user=group_user
            )
            categories = list(response.context["cl"].queryset.all())
            # list shows only categories linked to group
            self.assertEqual(categories, [category_grouped])

        with self.subTest("user cannot access not-linked category"):
            response = self.app.get(
                reverse(
                    "admin:pdc_category_change",
                    kwargs={"object_id": category_general.id},
                ),
                user=group_user,
            )
            # status code is 302 when object is not found and redirects to admin index
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.follow().request.path, "/admin/")

    def test_access_categories_cannot_be_edited_by_restricted(self):
        group = GroupFactory()
        group_user = UserFactory(is_staff=True)
        group_user.user_permissions.add(
            Permission.objects.get(codename="change_category"),
        )
        group_user.groups.add(group)

        category = CategoryFactory(path="grouped", name="grouped", published=True)
        category.access_groups.add(group)
        response = self.app.get(
            reverse(
                "admin:pdc_category_change",
                kwargs={"object_id": category.id},
            ),
            user=group_user,
        )
        self.assertIn("name", response.form.fields)
        self.assertNotIn("access_groups", response.form.fields)

    @patch("open_inwoner.openzaak.models.OpenZaakConfig.get_solo")
    def test_user_can_link_zaaktypen_if_category_filtering_with_zaken_feature_flag_enabled(
        self, mock_solo
    ):
        mock_solo.return_value.enable_categories_filtering_with_zaken = True

        ZaakTypeConfigFactory.create(identificatie="001")

        category = CategoryFactory(path="0006", slug="foo6", published=False)
        form = self.app.get(
            reverse("admin:pdc_category_change", kwargs={"object_id": category.pk}),
            user=self.user,
        ).form

        form["zaaktypen"] = "001"
        response = form.submit("_save")

        self.assertEqual(response.status_code, 302)

        category.refresh_from_db()

        self.assertEqual(category.zaaktypen, ["001"])

    @patch("open_inwoner.openzaak.models.OpenZaakConfig.get_solo")
    def test_user_cannot_link_zaaktypen_if_category_filtering_with_zaken_feature_flag_disabled(
        self, mock_solo
    ):
        mock_solo.return_value.enable_categories_filtering_with_zaken = False

        ZaakTypeConfigFactory.create(identificatie="001")

        category = CategoryFactory(path="0006", slug="foo6", published=False)
        form = self.app.get(
            reverse("admin:pdc_category_change", kwargs={"object_id": category.pk}),
            user=self.user,
        ).form

        form["zaaktypen"] = "001"
        response = form.submit()

        self.assertEqual(response.status_code, 200)

        error_msg = _(
            "The feature flag to enable category visibility based on zaken is currently disabled. "
            "This should be enabled via the admin interface before this Category can be linked to zaaktypen."
        )

        self.assertEqual(response.context["errors"], [[error_msg]])

        category.refresh_from_db()

        self.assertFalse(category.zaaktypen, [])
