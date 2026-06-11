from django.test import TestCase

from open_inwoner.openklant.models import DigitaalAdresKlant2Mapping

from .factories import DigitaalAdresKlant2MappingFactory


class DigitaalAdresKlant2MappingTests(TestCase):
    def test_str(self):
        mapping = DigitaalAdresKlant2MappingFactory()
        self.assertIn(str(mapping.ok2_uuid), str(mapping))

    def test_cascade_delete_on_digital_address_delete(self):
        mapping = DigitaalAdresKlant2MappingFactory()
        mapping_pk = mapping.pk

        mapping.digital_address.delete()

        self.assertFalse(
            DigitaalAdresKlant2Mapping.objects.filter(pk=mapping_pk).exists()
        )

    def test_one_to_one_enforced(self):
        from django.db import IntegrityError

        mapping = DigitaalAdresKlant2MappingFactory()
        with self.assertRaises(IntegrityError):
            DigitaalAdresKlant2MappingFactory(digital_address=mapping.digital_address)
