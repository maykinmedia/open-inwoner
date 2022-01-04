from django.test import TestCase

from ..models import ProductLocation
from .factories import ProductLocationFactory


class ProductLocationTestCase(TestCase):
    def test_create(self):
        ProductLocationFactory.create(
            street="Keizersgracht",
            housenumber="117",
            postcode="1015CJ",
            city="Amsterdam",
        )

    def test_geocode(self):
        product_location = ProductLocationFactory.create(
            street="Keizersgracht",
            housenumber="117",
            postcode="1015 CJ",
            city="Amsterdam",
        )
        self.assertEqual(
            '{ "type": "Point", "coordinates": [ 4.8876515, 52.3775941 ] }',
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
        )
        self.assertEqual(
            '{"type": "Feature", "geometry": {"type": "Point", "coordinates": [4.8876515, 52.3775941]}, "properties": {"name": "Maykin Media", "street": "Keizersgracht", "housenumber": "117", "postcode": "1015 CJ", "city": "Amsterdam"}}',
            product_location.get_geojson_feature(),
        )

    def test_get_geojson_geometry(self):
        product_location = ProductLocationFactory.create(
            street="Keizersgracht",
            housenumber="117",
            postcode="1015 CJ",
            city="Amsterdam",
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
        ProductLocationFactory.create(
            name="Maykin Media",
            street="Keizersgracht",
            housenumber="117",
            postcode="1015 CJ",
            city="Amsterdam",
        )
        ProductLocationFactory.create(
            name="Anne Frank Huis",
            street="Westermarkt",
            housenumber="20",
            postcode="1016 GV",
            city="Amsterdam",
        )
        self.assertEqual(
            '{"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [4.8876515, 52.3775941]}, "properties": {"name": "Maykin Media", "street": "Keizersgracht", "housenumber": "117", "postcode": "1015 CJ", "city": "Amsterdam"}}, {"type": "Feature", "geometry": {"type": "Point", "coordinates": [4.884554379441582, 52.3744749]}, "properties": {"name": "Anne Frank Huis", "street": "Westermarkt", "housenumber": "20", "postcode": "1016 GV", "city": "Amsterdam"}}]}',
            ProductLocation.objects.all().get_geojson_feature_collection(),
        )

    def test_queryset_centroid(self):
        ProductLocationFactory.create(
            street="Keizersgracht",
            housenumber="117",
            postcode="1015 CJ",
            city="Amsterdam",
        )
        ProductLocationFactory.create(
            street="Westermarkt",
            housenumber="20",
            postcode="1016 GV",
            city="Amsterdam",
        )
        self.assertEqual(
            "4.886102939720791", ProductLocation.objects.all().get_centroid()["lng"]
        )
        self.assertEqual(
            "52.3760345", ProductLocation.objects.all().get_centroid()["lat"]
        )
