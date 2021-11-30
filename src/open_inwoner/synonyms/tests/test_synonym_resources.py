from collections import OrderedDict

from django.core.exceptions import ValidationError
from django.test import TestCase

import tablib

from ..models import Synonym
from ..resources import SynonymResource
from .factories import SynonymFactory


class TestSynonymImportResource(TestCase):
    def setUp(self):
        self.synonym = SynonymFactory.create()
        self.resource = SynonymResource()

    def test_import_saves_term_and_synonyms(self):
        dataset = tablib.Dataset(
            [self.synonym.term, self.synonym.synonyms],
            headers=[
                "Term",
                "UF",
            ],
        )
        self.resource.import_data(dataset)
        qs = Synonym.objects.filter(term=self.synonym.term)

        self.assertEqual(qs.count(), 1)

    def test_import_raises_validation_error_with_wrong_headers(self):
        dataset = tablib.Dataset(
            [self.synonym.term, self.synonym.synonyms],
            headers=[
                "Wrong header",
                "Another wrong header",
            ],
        )
        with self.assertRaises(ValidationError) as e:
            self.resource.import_data(dataset, raise_errors=True)

        self.assertEqual(
            e.exception.message_dict,
            {
                "term": ["Dit veld kan niet leeg zijn"],
                "synonyms": ["Dit veld mag niet leeg zijn."],
            },
        )


class TestSynonymExportResource(TestCase):
    def setUp(self):
        self.synonym = SynonymFactory()
        self.resource = SynonymResource()

    def test_export_returns_expected_row(self):
        dataset = self.resource.export()

        self.assertEqual(
            dataset.dict,
            [
                OrderedDict(
                    [
                        (dataset.headers[0], self.synonym.term),
                        (dataset.headers[1], ", ".join(self.synonym.synonyms)),
                    ]
                ),
            ],
        )
