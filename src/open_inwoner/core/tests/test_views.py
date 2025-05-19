from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.utils.crypto import get_random_string

from open_inwoner.accounts.tests.factories import (
    DigidUserFactory,
    eHerkenningUserFactory,
)
from open_inwoner.pdc.tests.factories import CategoryFactory, ProductFactory

from ..views import _get_category_data_for_user


class SitemapCategoryDataTest(TestCase):
    def test_display_categories_simple(self):
        """No children, no products"""
        anon_user = AnonymousUser()
        category = CategoryFactory()

        res = _get_category_data_for_user(category, anon_user)

        self.assertEqual(res["category"], category)
        self.assertEqual(len(res["sub_categories"]), 0)
        self.assertEqual(list(res["products"]), [])

    def test_display_category_children(self):
        """Test display of category children, no nesting, no products"""
        anon_user = AnonymousUser()

        scenarios = [
            (True, True, 2),
            (True, False, 1),
            (False, True, 1),
            (False, False, 1),
        ]
        for published, visible, result in scenarios:
            with self.subTest(f"published: {published}, visible: {visible}"):
                root_category = CategoryFactory()
                # sanity check: one category is always visible
                root_category.add_child(
                    slug=get_random_string(length=8),
                    published=True,
                    visible_for_anonymous=True,
                )
                root_category.add_child(
                    slug=f"child2-published-{published}-visible-{visible}",
                    published=published,
                    visible_for_anonymous=visible,
                )

                res = _get_category_data_for_user(root_category, anon_user)

                self.assertEqual(len(res["sub_categories"]), result)

    def test_display_category_products(self):
        """Test display of category products, no children"""
        anon_user = AnonymousUser()

        scenarios = [(True, 2), (False, 1)]
        for published, result in scenarios:
            with self.subTest(f"published: {published}"):
                root_category = CategoryFactory()
                # sanity check: one product is always visible
                ProductFactory(
                    name=get_random_string(length=8),
                    categories=(root_category,),
                )
                ProductFactory(
                    name=get_random_string(length=8),
                    categories=(root_category,),
                    published=published,
                )

                res = _get_category_data_for_user(root_category, anon_user)

                self.assertEqual(len(res["products"]), result)

    def test_display_categories_nested(self):
        """Test display of nested category structure"""
        anon_user = AnonymousUser()

        root_category = CategoryFactory()
        # children
        root_child1 = root_category.add_child(
            name="root child 1",
            slug="root-child-1",
            published=True,
            visible_for_anonymous=True,
        )
        root_child2 = root_category.add_child(
            name="root child 2",
            slug="root-child-2",
            published=True,
            visible_for_anonymous=True,
        )
        root_category.add_child(
            name="root child invisible",
            slug="root-child-invisible",
            published=True,
            visible_for_anonymous=False,
        )
        # nested children
        nested_child_1 = root_child1.add_child(
            name="nested child 1",
            slug="nested-child-1",
            published=True,
            visible_for_anonymous=True,
        )
        nested_child_2 = root_child1.add_child(
            name="nested child 2",
            slug="nested-child-2",
            published=True,
            visible_for_anonymous=True,
        )
        # products
        prod1 = ProductFactory(
            name="prod1",
            categories=(nested_child_1,),
            published=True,
        )
        ProductFactory(
            name="prod2",
            categories=(nested_child_1,),
            published=False,
        )

        res = _get_category_data_for_user(root_category, anon_user)

        # Unfortunately we cannot use `self.assertEqual` on `res` since
        # `res` contains empty instances of `ProductQueryset` for which
        # `==` gives the wrong result; hence we need to resort to
        # piecemeal asserts

        # root
        self.assertEqual(res["category"], root_category)
        self.assertEqual(list(res["products"]), [])

        # sub categories level 1
        sub_categories = res["sub_categories"]
        self.assertEqual(len(sub_categories), 2)

        child1 = sub_categories[0]
        self.assertEqual(child1["category"], root_child1)
        self.assertEqual(list(child1["products"]), [])

        child2 = sub_categories[1]
        self.assertEqual(child2["category"], root_child2)
        self.assertEqual(list(child2["products"]), [])

        # sub categories level 2
        sub_sub_categories = child1["sub_categories"]
        self.assertEqual(len(sub_sub_categories), 2)

        nested_1 = sub_sub_categories[0]
        self.assertEqual(nested_1["category"], nested_child_1)
        self.assertEqual(list(nested_1["products"]), [prod1])

        nested_2 = sub_sub_categories[1]
        self.assertEqual(nested_2["category"], nested_child_2)
        self.assertEqual(list(nested_2["products"]), [])

    def test_display_category_visibility(self):
        """Test restriction of visibility for different users"""
        anon_user = AnonymousUser()
        digid_user = DigidUserFactory()
        eherkenning_user = eHerkenningUserFactory()

        scenarios_anon = [
            (True, True, True, 2),
            (True, True, False, 2),
            (True, False, True, 2),
            (True, False, False, 2),
            (False, True, True, 1),
            (False, True, False, 1),
            (False, False, True, 1),
            (False, False, False, 1),
        ]
        for visible_anon, visible_citizen, visible_eh, res_anon in scenarios_anon:
            with self.subTest(
                f"Scenario for anon user: {visible_anon}, {visible_citizen}, {visible_eh}"
            ):
                root_category = CategoryFactory()
                root_category.add_child(
                    name="root child 1",
                    slug=get_random_string(length=8),
                    published=True,
                    visible_for_anonymous=True,
                    visible_for_citizens=True,
                    visible_for_companies=True,
                )
                root_category.add_child(
                    name="root child 2",
                    slug=get_random_string(length=8),
                    published=True,
                    visible_for_anonymous=visible_anon,
                    visible_for_citizens=visible_citizen,
                    visible_for_companies=visible_eh,
                )

                res = _get_category_data_for_user(root_category, anon_user)

                self.assertEqual(len(res["sub_categories"]), res_anon)

        scenarios_citizen = [
            (True, True, True, 2),
            (True, True, False, 2),
            (True, False, True, 1),
            (True, False, False, 1),
            (False, True, True, 2),
            (False, True, False, 2),
            (False, False, True, 1),
            (False, False, False, 1),
        ]
        for visible_anon, visible_citizen, visible_eh, res_citizen in scenarios_citizen:
            with self.subTest(
                f"Scenario for anon user: {visible_anon}, {visible_citizen}, {visible_eh}"
            ):
                root_category = CategoryFactory()
                root_category.add_child(
                    name="root child 1",
                    slug=get_random_string(length=8),
                    published=True,
                    visible_for_anonymous=True,
                    visible_for_citizens=True,
                    visible_for_companies=True,
                )
                root_category.add_child(
                    name="root child 2",
                    slug=get_random_string(length=8),
                    published=True,
                    visible_for_anonymous=visible_anon,
                    visible_for_citizens=visible_citizen,
                    visible_for_companies=visible_eh,
                )

                res = _get_category_data_for_user(root_category, digid_user)

                self.assertEqual(len(res["sub_categories"]), res_citizen)

        scenarios_company = [
            (True, True, True, 2),
            (True, True, False, 1),
            (True, False, True, 2),
            (True, False, False, 1),
            (False, True, True, 2),
            (False, True, False, 1),
            (False, False, True, 2),
            (False, False, False, 1),
        ]
        for visible_anon, visible_citizen, visible_eh, res_company in scenarios_company:
            with self.subTest(
                f"Scenario for anon user: {visible_anon}, {visible_citizen}, {visible_eh}"
            ):
                root_category = CategoryFactory()
                root_category.add_child(
                    name="root child 1",
                    slug=get_random_string(length=8),
                    published=True,
                    visible_for_anonymous=True,
                    visible_for_citizens=True,
                    visible_for_companies=True,
                )
                root_category.add_child(
                    name="root child 2",
                    slug=get_random_string(length=8),
                    published=True,
                    visible_for_anonymous=visible_anon,
                    visible_for_citizens=visible_citizen,
                    visible_for_companies=visible_eh,
                )

                res = _get_category_data_for_user(root_category, eherkenning_user)

                self.assertEqual(len(res["sub_categories"]), res_company)
