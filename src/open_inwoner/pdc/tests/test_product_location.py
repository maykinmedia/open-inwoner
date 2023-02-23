import json
from unittest.mock import patch

from django.contrib.gis.geos import Point
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import UserFactory

from ..models import ProductLocation
from .factories import ProductFactory, ProductLocationFactory


class ProductLocationTestCase(TestCase):
    @patch(
        "open_inwoner.pdc.models.mixins.geocode_address",
        return_value=Point(4.8876438, 52.37670043),
    )
    def test_geocode(self, mock_geocoding):
        product_location = ProductLocation(
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
        mock_geocoding.assert_called_once_with("Keizersgracht 117, 1015CJ Amsterdam")

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
            email="loc@example.com",
            phonenumber="+31666767676",
            geometry=Point(4.8876515, 52.3775941),
        )
        product = ProductFactory.create(locations=(product_location,))

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
                        "address_line_1": "Keizersgracht 117",
                        "address_line_2": "1015CJ Amsterdam",
                        "email": "loc@example.com",
                        "phonenumber": "+31666767676",
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
            email="loc@example.com",
            phonenumber="+31666767676",
        )
        self.assertEqual(
            {
                "name": "Maykin Media",
                "address_line_1": "Keizersgracht 117",
                "address_line_2": "1015CJ Amsterdam",
                "email": "loc@example.com",
                "phonenumber": "+31666767676",
            },
            product_location.get_serialized_fields(),
        )

    def test_queryset_get_geojson_feature_collection(self):
        product_location_1 = ProductLocationFactory.create(
            name="Gemeente Deventer",
            street="Grote Kerkhof",
            housenumber="4",
            postcode="7411 KT",
            city="Deventer",
            email="loc1@example.com",
            phonenumber="+31999767676",
            geometry=Point(6.155650, 52.251550),
        )
        product_location_2 = ProductLocationFactory.create(
            name="Gemeente Amsterdam",
            street="Lindengracht",
            housenumber="204",
            postcode="1015 KL",
            city="Amsterdam",
            email="loc2@example.com",
            phonenumber="+31666767676",
            geometry=Point(4.883400, 52.380260),
        )
        product_1 = ProductFactory(locations=(product_location_1,))
        product_2 = ProductFactory(locations=(product_location_1, product_location_2))
        self.assertEqual(
            json.dumps(
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [6.155650, 52.251550],
                            },
                            "properties": {
                                "name": "Gemeente Deventer",
                                "address_line_1": "Grote Kerkhof 4",
                                "address_line_2": "7411KT Deventer",
                                "email": "loc1@example.com",
                                "phonenumber": "+31999767676",
                            },
                        },
                        {
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [4.883400, 52.380260],
                            },
                            "properties": {
                                "name": "Gemeente Amsterdam",
                                "address_line_1": "Lindengracht 204",
                                "address_line_2": "1015KL Amsterdam",
                                "email": "loc2@example.com",
                                "phonenumber": "+31666767676",
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
    @patch("open_inwoner.pdc.models.mixins.geocode_address", side_effect=IndexError)
    def test_exception_is_handled_when_city_and_postcode_are_not_provided(
        self, mock_geocoding
    ):
        user = UserFactory(is_superuser=True, is_staff=True)

        response = self.app.get(reverse("admin:pdc_productlocation_add"), user=user)
        form = response.form
        form_response = form.submit("_save")

        self.assertListEqual(
            form_response.context["errors"],
            [
                [_("Dit veld is vereist.")],
                [_("Dit veld is vereist.")],
                [_("No location data was provided")],
            ],
        )
        mock_geocoding.assert_called_once_with(" ,  ")
