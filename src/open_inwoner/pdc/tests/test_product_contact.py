from django.test import TestCase

from open_inwoner.pdc.tests.factories import OrganizationFactory, ProductContactFactory


class ProductContactTestCase(TestCase):
    def test_create(self):
        ProductContactFactory.create()

    def test_get_mailto_link(self):
        organization = OrganizationFactory.create(email="lorem@example.com")
        product_contact_1 = ProductContactFactory.create(
            organization=organization, email=""
        )
        product_contact_2 = ProductContactFactory.create(
            organization=organization, email="ipsum@example.com"
        )

        self.assertEqual(
            "mailto://lorem@example.com", product_contact_1.get_mailto_link()
        )
        self.assertEqual(
            "mailto://ipsum@example.com", product_contact_2.get_mailto_link()
        )

    def test_get_email(self):
        organization = OrganizationFactory.create(email="lorem@example.com")
        product_contact_1 = ProductContactFactory.create(
            organization=organization, email=""
        )
        product_contact_2 = ProductContactFactory.create(
            organization=organization, email="ipsum@example.com"
        )

        self.assertEqual("lorem@example.com", product_contact_1.get_email())
        self.assertEqual("ipsum@example.com", product_contact_2.get_email())

    def test_email(self):
        organization = OrganizationFactory.create(phonenumber="123456789")
        product_contact_1 = ProductContactFactory.create(
            organization=organization, phonenumber=""
        )
        product_contact_2 = ProductContactFactory.create(
            organization=organization, phonenumber="987654321"
        )

        self.assertEqual("123456789", product_contact_1.get_phone_number())
        self.assertEqual("987654321", product_contact_2.get_phone_number())
