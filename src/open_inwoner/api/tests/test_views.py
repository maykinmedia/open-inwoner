from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from open_inwoner.pdc.models import Category
from open_inwoner.pdc.tests.factories import CategoryFactory


class TestPDCLocation(APITestCase):
    def setUp(self):
        self.client = APIClient()

        self.root_category_1 = CategoryFactory.build()
        self.child_category_1 = CategoryFactory.build()
        self.grandchild_category = CategoryFactory.build()
        Category.add_root(instance=self.root_category_1)
        self.root_category_1.add_child(instance=self.child_category_1)
        self.child_category_1.add_child(instance=self.grandchild_category)

        self.root_category_2 = CategoryFactory.build()
        self.child_category_2 = CategoryFactory.build()
        Category.add_root(instance=self.root_category_2)
        self.root_category_2.add_child(instance=self.child_category_2)

    def test_list_categories_endpoint_returns_both_parent_and_children_categories(self):
        response = self.client.get(reverse("api:categories-list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            sorted(response.json(), key=lambda k: k["slug"]),
            sorted(
                [
                    {
                        "name": self.root_category_1.name,
                        "slug": self.root_category_1.slug,
                        "published": self.root_category_1.published,
                        "highlighted": self.root_category_1.highlighted,
                        "description": self.root_category_1.description,
                        "icon": None,
                        "image": None,
                        "products": [],
                        "questions": [],
                        "children": [
                            {
                                "url": f"http://testserver/api/categories/{self.child_category_1.slug}/",
                                "name": self.child_category_1.name,
                                "slug": self.child_category_1.slug,
                                "published": self.child_category_1.published,
                                "highlighted": self.child_category_1.highlighted,
                                "description": self.child_category_1.description,
                            }
                        ],
                    },
                    {
                        "name": self.root_category_2.name,
                        "slug": self.root_category_2.slug,
                        "published": self.root_category_2.published,
                        "highlighted": self.root_category_2.highlighted,
                        "description": self.root_category_2.description,
                        "icon": None,
                        "image": None,
                        "products": [],
                        "questions": [],
                        "children": [
                            {
                                "url": f"http://testserver/api/categories/{self.child_category_2.slug}/",
                                "name": self.child_category_2.name,
                                "slug": self.child_category_2.slug,
                                "published": self.child_category_2.published,
                                "highlighted": self.child_category_2.highlighted,
                                "description": self.child_category_2.description,
                            }
                        ],
                    },
                ],
                key=lambda k: k["slug"],
            ),
        )

    def test_category_detail_endpoint_returns_both_parent_and_children_categories(self):
        response = self.client.get(
            reverse(
                "api:categories-detail", kwargs={"slug": self.child_category_1.slug}
            ),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                "name": self.child_category_1.name,
                "slug": self.child_category_1.slug,
                "published": self.child_category_1.published,
                "highlighted": self.child_category_1.highlighted,
                "description": self.child_category_1.description,
                "icon": None,
                "image": None,
                "products": [],
                "questions": [],
                "children": [
                    {
                        "url": f"http://testserver/api/categories/{self.grandchild_category.slug}/",
                        "name": self.grandchild_category.name,
                        "slug": self.grandchild_category.slug,
                        "published": self.grandchild_category.published,
                        "highlighted": self.grandchild_category.highlighted,
                        "description": self.grandchild_category.description,
                    }
                ],
            },
        )
