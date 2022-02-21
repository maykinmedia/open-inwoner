import json

from django.contrib.gis.geos import Point
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import UserFactory

from ..models import ProductLocation
from .factories import ProductFactory, ProductLocationFactory


class ProductLocationTestCase(TestCase):
    def test_geocode(self):
        """FIXME this test request actual external API. Should be reworked"""
        product = ProductFactory.create()
        product_location = ProductLocation(
            product=product,
            street="Keizersgracht",
            housenumber="117",
            postcode="1015 CJ",
            city="Amsterdam",
        )
        product_location.clean()
        product_location.save()
        self.assertEqual(
            '{ "type": "Point", "coordinates": [ 4.8876438, 52.37670043 ] }',
            product_location.geometry.geojson,
        )

    def test_address_str(self):
        product_location = ProductLocationFactory.create(
            street="Keizersgracht",
            housenumber="117",
            postcode="1015 CJ",
            city="Amsterdam",
        )
        self.assertEqual(
            "Keizersgracht 117, 1015CJ Amsterdam", product_location.address_str
        )

    def test_address_line_1(self):
        product_location = ProductLocationFactory.create(
            street="Keizersgracht",
            housenumber="117",
            postcode="1015 CJ",
            city="Amsterdam",
        )
        self.assertEqual("Keizersgracht 117", product_location.address_line_1)

    def test_address_line_2(self):
        product_location = ProductLocationFactory.create(
            street="Keizersgracht",
            housenumber="117",
            postcode="1015 CJ",
            city="Amsterdam",
        )
        self.assertEqual("1015CJ Amsterdam", product_location.address_line_2)

    def test_get_geojson_feature(self):
        product_location = ProductLocationFactory.create(
            name="Maykin Media",
            street="Keizersgracht",
            housenumber="117",
            postcode="1015 CJ",
            city="Amsterdam",
            geometry=Point(4.8876515, 52.3775941),
        )
        self.assertEqual(
            json.dumps(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [4.8876515, 52.3775941],
                    },
                    "properties": {
                        "name": "Maykin Media",
                        "street": "Keizersgracht",
                        "housenumber": "117",
                        "postcode": "1015 CJ",
                        "city": "Amsterdam",
                        "url": product_location.product.get_absolute_url(),
                    },
                }
            ),
            product_location.get_geojson_feature(),
        )

    def test_get_geojson_geometry(self):
        product_location = ProductLocationFactory.create(
            street="Keizersgracht",
            housenumber="117",
            postcode="1015 CJ",
            city="Amsterdam",
            geometry=Point(4.8876515, 52.3775941),
        )
        self.assertEqual(
            '{ "type": "Point", "coordinates": [ 4.8876515, 52.3775941 ] }',
            product_location.get_geojson_geometry(),
        )

    def test_get_serialized_fields(self):
        product_location = ProductLocationFactory.create(
            name="Maykin Media",
            street="Keizersgracht",
            housenumber="117",
            postcode="1015 CJ",
            city="Amsterdam",
        )
        self.assertEqual(
            {
                "city": "Amsterdam",
                "housenumber": "117",
                "name": "Maykin Media",
                "postcode": "1015 CJ",
                "street": "Keizersgracht",
            },
            product_location.get_serialized_fields(),
        )

    def test_queryset_get_geojson_feature_collection(self):
        product_location_1 = ProductLocationFactory.create(
            name="Maykin Media",
            street="Keizersgracht",
            housenumber="117",
            postcode="1015 CJ",
            city="Amsterdam",
            geometry=Point(4.8876515, 52.3775941),
        )
        product_location_2 = ProductLocationFactory.create(
            name="Anne Frank Huis",
            street="Westermarkt",
            housenumber="20",
            postcode="1016 GV",
            city="Amsterdam",
            geometry=Point(4.884554379441582, 52.3744749),
        )
        self.assertEqual(
            json.dumps(
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [4.8876515, 52.3775941],
                            },
                            "properties": {
                                "name": "Maykin Media",
                                "street": "Keizersgracht",
                                "housenumber": "117",
                                "postcode": "1015 CJ",
                                "city": "Amsterdam",
                                "url": product_location_1.product.get_absolute_url(),
                            },
                        },
                        {
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [4.884554379441582, 52.3744749],
                            },
                            "properties": {
                                "name": "Anne Frank Huis",
                                "street": "Westermarkt",
                                "housenumber": "20",
                                "postcode": "1016 GV",
                                "city": "Amsterdam",
                                "url": product_location_2.product.get_absolute_url(),
                            },
                        },
                    ],
                }
            ),
            ProductLocation.objects.all().get_geojson_feature_collection(),
        )

    def test_queryset_centroid(self):
        ProductLocationFactory.create(
            street="Keizersgracht",
            housenumber="117",
            postcode="1015 CJ",
            city="Amsterdam",
            geometry=Point(4.8876515, 52.3775941),
        )
        ProductLocationFactory.create(
            street="Westermarkt",
            housenumber="20",
            postcode="1016 GV",
            city="Amsterdam",
            geometry=Point(4.884554379441582, 52.3744749),
        )
        self.assertIn(
            "4.88610293972079", ProductLocation.objects.all().get_centroid()["lng"]
        )
        self.assertEqual(
            "52.3760345", ProductLocation.objects.all().get_centroid()["lat"]
        )


class TestLocationFormInput(WebTest):
    def test_exception_is_handled_when_city_and_postcode_are_not_provided(self):
        product = ProductFactory()
        user = UserFactory(is_superuser=True, is_staff=True)

        response = self.app.get(reverse("admin:pdc_productlocation_add"), user=user)
        form = response.form
        form["product"] = product.pk
        form_response = form.submit("_save")

        self.assertListEqual(
            form_response.context["errors"],
            [
                [_("Dit veld is vereist.")],
                [_("Dit veld is vereist.")],
                [_("No location data was provided")],
            ],
        )
