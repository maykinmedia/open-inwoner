from ipaddress import IPv4Address, IPv6Address

from django.test import TestCase

from pydantic import BaseModel, HttpUrl

from ..api import JSONEncoderMixin


class TestDummy(JSONEncoderMixin, BaseModel):
    ipv4: IPv4Address
    ipv6: IPv6Address
    url: HttpUrl


class JSONEncoderTest(TestCase):
    def test_encode(self):
        user_data = TestDummy(
            ipv4="127.0.0.1",
            ipv6="2345:0425:2CA1:0:0:0567:5673:23b5",
            url="http://source.url",
        )

        self.assertEqual(
            user_data.model_dump(),
            {
                "ipv4": "127.0.0.1",
                "ipv6": "2345:425:2ca1::567:5673:23b5",
                "url": "http://source.url/",
            },
        )
