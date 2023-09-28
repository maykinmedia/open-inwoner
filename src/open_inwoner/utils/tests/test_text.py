from django.test import TestCase

from open_inwoner.utils.text import middle_truncate


class TextTestCase(TestCase):
    def test_middle_truncate(self):
        self.assertEqual(middle_truncate("abc", 5), "abc")
        self.assertEqual(
            middle_truncate("a_pretty_long_file_name.jpg", 23), "a_pretty...le_name.jpg"
        )
