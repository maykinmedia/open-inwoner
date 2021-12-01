from django.test import TestCase

from open_inwoner.pdc.tests.factories import ProductFactory

from ..searches import search_autocomplete
from .utils import ESMixin


class AutocompleteTests(ESMixin, TestCase):
    def test_autocomplete_on_name(self):
        ProductFactory.create(name="Name", keywords=["Keyword"])
        ProductFactory.create(name="New", keywords=["Key"])
        self.update_index()

        result = search_autocomplete("n")

        self.assertEqual(result.options, ["Name", "New"])

        suggester_name, suggester_keyword = result.suggesters
        self.assertEqual(suggester_name.options, ["Name", "New"])
        self.assertEqual(suggester_keyword.options, [])

    def test_autocomplete_on_keyword(self):
        ProductFactory.create(name="Name", keywords=["Keyword"])
        ProductFactory.create(name="New", keywords=["Key"])
        self.update_index()

        result = search_autocomplete("k")

        self.assertEqual(result.options, ["Key", "Keyword"])

        suggester_name, suggester_keyword = result.suggesters
        self.assertEqual(suggester_name.options, [])
        self.assertEqual(suggester_keyword.options, ["Key", "Keyword"])

    def test_autocomplete_on_name_and_keyword(self):
        ProductFactory.create(name="Some name1", keywords=["Some keyword1"])
        ProductFactory.create(name="Some name2", keywords=["Some keyword2"])
        self.update_index()

        result = search_autocomplete("s")

        self.assertEqual(
            result.options,
            ["Some name1", "Some name2", "Some keyword1", "Some keyword2"],
        )

        suggester_name, suggester_keyword = result.suggesters
        self.assertEqual(suggester_name.options, ["Some name1", "Some name2"])
        self.assertEqual(suggester_keyword.options, ["Some keyword1", "Some keyword2"])

    def test_autocomplete_deduplicated(self):
        ProductFactory.create(name="Some", keywords=["Other"])
        ProductFactory.create(name="Other", keywords=["Some"])
        self.update_index()

        result = search_autocomplete("s")

        self.assertEqual(result.options, ["Some"])

        suggester_name, suggester_keyword = result.suggesters
        self.assertEqual(suggester_name.options, ["Some"])
        self.assertEqual(suggester_keyword.options, ["Some"])

    def test_autocomplete_no_result(self):
        ProductFactory.create(name="Some", keywords=["Other"])
        self.update_index()

        result = search_autocomplete("m")

        self.assertEqual(result.options, [])

        suggester_name, suggester_keyword = result.suggesters
        self.assertEqual(suggester_name.options, [])
        self.assertEqual(suggester_keyword.options, [])
