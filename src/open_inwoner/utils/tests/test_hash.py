from collections import deque
from datetime import date, datetime
from uuid import UUID, uuid4

from django.test import TestCase

from open_inwoner.utils.hash import pyhash_value


class PyHashTest(TestCase):
    def test_pyhash_value(self):
        self.assertEqual(pyhash_value(123), pyhash_value(123))
        self.assertEqual(pyhash_value("123"), pyhash_value("123"))
        self.assertEqual(pyhash_value(True), pyhash_value(True))

        self.assertEqual(
            # list
            pyhash_value([1, 2, 3]),
            pyhash_value([1, 2, 3]),
        )
        self.assertEqual(
            # tuple
            pyhash_value((1, 2, 3)),
            pyhash_value((1, 2, 3)),
        )
        self.assertEqual(
            # set
            pyhash_value({1, 2, 3}),
            pyhash_value({3, 2, 1}),
        )
        self.assertEqual(
            # mixed list/tuple
            pyhash_value((1, 2, 3)),
            pyhash_value([1, 2, 3]),
        )
        self.assertEqual(
            pyhash_value(date(2022, 1, 1)),
            pyhash_value(date(2022, 1, 1)),
        )
        self.assertEqual(
            pyhash_value(datetime(2022, 1, 1)),
            pyhash_value(datetime(2022, 1, 1)),
        )
        self.assertEqual(
            # mixed ordering
            pyhash_value({"a": (1, 2, 3), "b": "xyz"}),
            pyhash_value({"b": "xyz", "a": (1, 2, 3)}),
        )
        uuid = str(uuid4())
        self.assertEqual(
            # any hashable
            pyhash_value(UUID(uuid)),
            pyhash_value(UUID(uuid)),
        )
        self.assertEqual(
            # nested kitchensink
            pyhash_value({"a": {"b": (1, date(2022, 1, 1), UUID(uuid))}}),
            pyhash_value({"a": {"b": (1, date(2022, 1, 1), UUID(uuid))}}),
        )
        with self.assertRaises(TypeError):
            # try an unsupported un-hashable
            pyhash_value(deque([1, 2, 3]))
