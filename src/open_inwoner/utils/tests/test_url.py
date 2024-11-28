from uuid import UUID

from django.test import TestCase, override_settings

from open_inwoner.utils.url import (
    get_next_url_from,
    get_next_url_param,
    prepend_next_url_param,
    uuid_from_url,
)


class MockRequest:
    def __init__(self, GET=None):
        self.GET = GET or dict()

    def get_host(self):
        return "testserver"


class URLTest(TestCase):
    @override_settings(IS_HTTPS=True)
    def test_get_next_url_from(self):
        request = MockRequest()

        with self.subTest("defaults"):
            self.assertEqual(get_next_url_from(request), "")
            self.assertEqual(get_next_url_from(request, default="/foo"), "/foo")

        with self.subTest("normal"):
            request.GET["next"] = "/bar"
            self.assertEqual(
                get_next_url_from(
                    request,
                ),
                "/bar",
            )

        with self.subTest("http same host not valid"):
            request.GET["next"] = "http://testserver/bar"
            self.assertEqual(
                get_next_url_from(
                    request,
                ),
                "",
            )
        with self.subTest("https same host is valid"):
            request.GET["next"] = "https://testserver/bar"
            self.assertEqual(
                get_next_url_from(
                    request,
                ),
                "https://testserver/bar",
            )

        with self.subTest("http bad host not valid"):
            request.GET["next"] = "http://bazz/bar"
            self.assertEqual(
                get_next_url_from(
                    request,
                ),
                "",
            )
        with self.subTest("https bad host not valid"):
            request.GET["next"] = "https://bazz/bar"
            self.assertEqual(
                get_next_url_from(
                    request,
                ),
                "",
            )

    def test_get_next_url_param(self):
        self.assertEqual(get_next_url_param("http://testserver/"), "")
        self.assertEqual(get_next_url_param("http://testserver/?next="), "")
        self.assertEqual(get_next_url_param("http://testserver/?next=%2Ffoo"), "/foo")
        self.assertEqual(
            get_next_url_param("http://testserver/?next=%2Fbar%3Fnext%3D%252Ffoo"),
            "/bar?next=%2Ffoo",
        )

    def test_prepend_next_url_param(self):
        url = prepend_next_url_param("http://testserver/", "/foo")
        self.assertEqual(url, "http://testserver/?next=%2Ffoo")

        url = prepend_next_url_param(url, "/bar")
        self.assertEqual(url, "http://testserver/?next=%2Fbar%3Fnext%3D%252Ffoo")

        url = prepend_next_url_param(url, "/bazz")
        self.assertEqual(
            url,
            "http://testserver/?next=%2Fbazz%3Fnext%3D%252Fbar%253Fnext%253D%25252Ffoo",
        )

        # now let's go in reverse
        param = get_next_url_param(url)
        self.assertEqual(param, "/bazz?next=%2Fbar%3Fnext%3D%252Ffoo")

        param = get_next_url_param(param)
        self.assertEqual(param, "/bar?next=%2Ffoo")

        param = get_next_url_param(param)
        self.assertEqual(param, "/foo")


class UUIDfromURLTest(TestCase):
    def test_uuid_from_url(self):
        testcases = [
            (
                "https://example.com/123e4567-e89b-12d3-a456-426614174000",
                UUID("123e4567-e89b-12d3-a456-426614174000"),
            ),
            (
                "https://example.com/123e4567-e89b-12d3-a456-426614174000/987fEDCB-A987-654c-B321-123456789ABC",
                [
                    UUID("123e4567-e89b-12d3-a456-426614174000"),
                    UUID("987fEDCB-A987-654c-B321-123456789ABC"),
                ],
            ),
            ("https://example.com/aaa-aaaaaa-bbbb-ccccc-426614174000", None),
        ]
        for url, expected in testcases:
            with self.subTest():
                actual = uuid_from_url(url, allow_multiple=True)
                self.assertEqual(actual, expected)

    def test_uuid_from_url_no_multiple(self):
        url = "https://example.com/123e4567-e89b-12d3-a456-426614174000/987fEDCB-A987-654c-B321-123456789ABC"

        with self.assertRaises(ValueError):
            uuid_from_url(url)
