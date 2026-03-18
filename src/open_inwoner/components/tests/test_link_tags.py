from django.test import SimpleTestCase

from open_inwoner.components.templatetags.link_tags import (
    add_attr_consuming_service_index,
)


class AddAttrConsumingServiceIndexFilterTest(SimpleTestCase):
    def test_appends_index_when_set(self):
        result = add_attr_consuming_service_index("/eherkenning/login/", "9052")
        self.assertEqual(
            result, "/eherkenning/login/?attr_consuming_service_index=9052"
        )

    def test_no_op_when_empty_string(self):
        result = add_attr_consuming_service_index("/eherkenning/login/", "")
        self.assertEqual(result, "/eherkenning/login/")

    def test_no_op_when_none(self):
        result = add_attr_consuming_service_index("/eherkenning/login/", None)
        self.assertEqual(result, "/eherkenning/login/")

    def test_preserves_existing_query_params(self):
        result = add_attr_consuming_service_index(
            "/eherkenning/login/?next=%2F", "9052"
        )
        self.assertIn("next=%2F", result)
        self.assertIn("attr_consuming_service_index=9052", result)
