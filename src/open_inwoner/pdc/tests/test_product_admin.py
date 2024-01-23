from django.contrib.auth.models import Permission
from django.urls import reverse

from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import GroupFactory, UserFactory

from .factories import CategoryFactory, ProductFactory


class TestAdminProductForm(WebTest):
    def test_access_limited_to_linked_auth_groups(self):
        super_user = UserFactory(is_superuser=True, is_staff=True)

        group = GroupFactory()
        group_user = UserFactory(is_staff=True)
        group_user.user_permissions.add(Permission.objects.get(codename="view_product"))
        group_user.groups.add(group)

        category_general = CategoryFactory(
            path="everyone", name="everyone", published=True
        )
        category_grouped = CategoryFactory(
            path="grouped", name="grouped", published=True
        )
        category_grouped.access_groups.add(group)

        product_general = ProductFactory(name="General Product")
        category_general.products.add(product_general)

        product_grouped = ProductFactory(name="Grouped Product")
        category_grouped.products.add(product_grouped)

        with self.subTest("superuser sees all in list"):
            response = self.app.get(
                reverse("admin:pdc_product_changelist"), user=super_user
            )
            products = list(response.context["cl"].queryset.all())
            # list shows all categories
            self.assertEqual(products, [product_general, product_grouped])

        with self.subTest("user list is limited by group"):
            response = self.app.get(
                reverse("admin:pdc_product_changelist"), user=group_user
            )
            categories = list(response.context["cl"].queryset.all())
            # list shows only product in categories linked to group
            self.assertEqual(categories, [product_grouped])

        with self.subTest("user cannot access not-linked category"):
            response = self.app.get(
                reverse(
                    "admin:pdc_product_change",
                    kwargs={"object_id": product_general.id},
                ),
                user=group_user,
            )
            # status code is 302 when object is not found and redirects to admin index
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.follow().request.path, "/admin/")

    def test_product_keeps_mixed_restricted_and_unrestricted_categories(self):
        super_user = UserFactory(is_superuser=True, is_staff=True)

        group = GroupFactory()
        group_user = UserFactory(is_staff=True)
        group_user.user_permissions.add(
            Permission.objects.get(codename="view_product"),
            Permission.objects.get(codename="change_product"),
        )
        group_user.groups.add(group)

        category_general = CategoryFactory(
            path="everyone", name="everyone", published=True
        )
        category_grouped = CategoryFactory(
            path="grouped", name="grouped", published=True
        )
        category_extra = CategoryFactory(path="grouped", name="extra", published=True)
        group.managed_categories.add(category_grouped)
        group.managed_categories.add(category_extra)

        product = ProductFactory(name="Product")
        product.categories.add(category_general)
        product.categories.add(category_grouped)

        url = reverse("admin:pdc_product_change", kwargs={"object_id": product.id})

        with self.subTest("superuser"):
            response = self.app.get(url, user=super_user)

            # all categories visible
            self.assertEqual(len(response.form["categories"].options), 3)
            self.assertEqual(
                set(response.form["categories"].value),
                {str(category_general.id), str(category_grouped.id)},
            )
            response = response.form.submit("_continue").follow()

            # no changes on resubmit
            self.assertEqual(
                set(product.categories.all()), {category_general, category_grouped}
            )

            # sanity check with different combinations
            response.form["categories"].select_multiple(
                value=[str(category_general.id), str(category_extra.id)]
            )
            response = response.form.submit("_continue").follow()
            self.assertEqual(
                set(product.categories.all()), {category_general, category_extra}
            )

            # sanity check with different combinations
            response.form["categories"].select_multiple(value=[str(category_extra.id)])
            response = response.form.submit("_continue").follow()
            self.assertEqual(set(product.categories.all()), {category_extra})

        product.categories.set([category_general, category_grouped])

        with self.subTest("restricted user"):
            response = self.app.get(url, user=group_user)

            # only our restricted
            self.assertEqual(len(response.form["categories"].options), 2)
            self.assertEqual(
                set(response.form["categories"].value),
                {str(category_grouped.id)},
            )
            response = response.form.submit("_continue").follow()

            # on resubmit the non-group category is still there
            self.assertEqual(
                set(product.categories.all()), {category_general, category_grouped}
            )
            # select different category
            response.form["categories"].select_multiple(value=[str(category_extra.id)])
            response.form.submit()

            # swapped different category but the non-group category is still there
            self.assertEqual(
                set(product.categories.all()), {category_general, category_extra}
            )
