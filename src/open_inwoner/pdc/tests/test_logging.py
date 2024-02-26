import logging

from django.urls import reverse
from django.utils.translation import gettext as _

import tablib
from django_webtest import WebTest
from freezegun import freeze_time
from maykin_2fa.test import disable_admin_mfa
from timeline_logger.models import TimelineLog
from webtest import Upload

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.utils.logentry import LOG_ACTIONS

from ..models.category import Category
from ..models.product import Product
from .factories import CategoryFactory, ProductFactory


@disable_admin_mfa()
@freeze_time("2021-10-18 13:00:00")
class TestProductLogging(WebTest):
    def setUp(self):
        self.category = CategoryFactory()
        self.product = ProductFactory.build(categories=(self.category,))
        self.user = UserFactory(is_superuser=True, is_staff=True)

    def test_addition(self):
        response = self.app.get(reverse("admin:pdc_product_add"), user=self.user)
        form = response.forms["product_form"]
        form["name"] = self.product.name
        form["slug"] = self.product.slug
        form["content"] = self.product.content
        form["summary"] = self.product.summary
        form["categories"] = [self.category.id]
        form["costs"] = 0.0
        form.submit()
        product = Product.objects.filter(slug=self.product.slug).first()
        log_entry = TimelineLog.objects.last()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.id, product.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("Toegevoegd."),
                "action_flag": [1, "Addition"],
                "content_object_repr": product.name,
            },
        )

    def test_change(self):
        self.product.save()
        self.product.categories.add(self.category.id)
        response = self.app.get(
            reverse("admin:pdc_product_change", kwargs={"object_id": self.product.id}),
            user=self.user,
        )
        form = response.forms["product_form"]
        form["content"] = "Updated content"
        form.submit()
        log_entry = TimelineLog.objects.last()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )

        self.assertEqual(log_entry.content_object.id, self.product.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("Content gewijzigd."),
                "action_flag": [2, "Change"],
                "content_object_repr": self.product.name,
            },
        )

    def test_deletion(self):
        self.product.save()
        self.product.categories.add(self.category.id)
        response = self.app.get(
            reverse("admin:pdc_product_delete", kwargs={"object_id": self.product.id}),
            user=self.user,
        )
        form = response.forms[0]
        form.submit()
        products = Product.objects.all().count()

        self.assertEqual(products, 0)

    def test_import_is_logged(self):
        dataset = tablib.Dataset(
            [
                self.product.name,
                self.product.summary,
                self.product.content,
                self.category.slug,
                "",
                "",
                "",
                "",
                "",
                "",
            ],
            headers=[
                "name",
                "summary",
                "content",
                "categories",
                "slug",
                "link",
                "related_products",
                "tags",
                "costs",
                "organizations",
            ],
        )
        byte_data = str.encode(dataset.export("csv"))
        response = self.app.get(reverse("admin:pdc_product_import"), user=self.user)
        form = response.forms[0]
        form["import_file"] = Upload("products.csv", byte_data, "text/csv")
        form["input_format"] = 1
        response_form = form.submit().forms[0]
        response_form.submit()
        log_entry = TimelineLog.objects.last()
        product = Product.objects.first()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.id, product.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("new through import_export"),
                "action_flag": list(LOG_ACTIONS[1]),
                "content_object_repr": self.product.name,
            },
        )

    def test_export_is_logged(self):
        ProductFactory(categories=(self.category,))
        response = self.app.get(reverse("admin:pdc_product_export"), user=self.user)
        form = response.forms[0]
        form["file_format"] = 1
        form.submit()
        log_entry = TimelineLog.objects.last()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.user.id, self.user.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("products were exported"),
                "log_level": logging.INFO,
                "action_flag": list(LOG_ACTIONS[5]),
                "content_object_repr": "",
            },
        )


@disable_admin_mfa()
@freeze_time("2021-10-18 13:00:00")
class TestCategoryLogging(WebTest):
    def setUp(self):
        self.category = CategoryFactory.build()
        self.user = UserFactory(is_superuser=True, is_staff=True)

    def test_addition(self):
        response = self.app.get(reverse("admin:pdc_category_add"), user=self.user)
        form = response.forms["category_form"]
        form["name"] = self.category.name
        form["slug"] = self.category.slug
        form.submit()
        category = Category.objects.filter(slug=self.category.slug).first()
        log_entry = TimelineLog.objects.last()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.id, category.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("Toegevoegd."),
                "action_flag": [1, "Addition"],
                "content_object_repr": self.category.name,
            },
        )

    def test_change(self):
        category = CategoryFactory()
        response = self.app.get(
            reverse("admin:pdc_category_change", kwargs={"object_id": category.id}),
            user=self.user,
        )
        form = response.forms["category_form"]
        form["description"] = "Updated description"
        form.submit()
        log_entry = TimelineLog.objects.last()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )

        self.assertEqual(log_entry.content_object.id, category.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": "Omschrijving, Ten opzichte van and Zaaktypen gewijzigd.",
                "action_flag": [2, "Change"],
                "content_object_repr": category.name,
            },
        )

    def test_deletion(self):
        category = CategoryFactory()
        response = self.app.get(
            reverse("admin:pdc_category_delete", kwargs={"object_id": category.id}),
            user=self.user,
        )
        form = response.forms[0]
        form.submit()
        categories = Category.objects.all().count()

        self.assertEqual(categories, 0)

    def test_import_is_logged(self):
        category = CategoryFactory.build()
        dataset = tablib.Dataset(
            [
                self.category.name,
                self.category.description,
                "",
            ],
            headers=[
                "name",
                "description",
                "slug",
            ],
        )
        byte_data = str.encode(dataset.export("csv"))
        response = self.app.get(reverse("admin:pdc_category_import"), user=self.user)
        form = response.forms[0]
        form["import_file"] = Upload("categories.csv", byte_data, "text/csv")
        form["input_format"] = 1
        response_form = form.submit().forms[0]
        response_form.submit()
        log_entry = TimelineLog.objects.last()
        category = Category.objects.first()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.id, category.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("new through import_export"),
                "action_flag": list(LOG_ACTIONS[1]),
                "content_object_repr": self.category.name,
            },
        )

    def test_export_is_logged(self):
        CategoryFactory()
        response = self.app.get(reverse("admin:pdc_category_export"), user=self.user)
        form = response.forms[0]
        form["file_format"] = 1
        form.submit()
        log_entry = TimelineLog.objects.last()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.user.id, self.user.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("categories were exported"),
                "log_level": logging.INFO,
                "action_flag": list(LOG_ACTIONS[5]),
                "content_object_repr": "",
            },
        )
