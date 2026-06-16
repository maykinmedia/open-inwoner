from django.test import tag

from open_inwoner.utils.tests.test_migrations import TestSuccessfulMigrations


@tag("migrations")
class TestPhoneNumberBackfill(TestSuccessfulMigrations):
    """
    Phone numbers on User are backfilled as DigitalAddress records.

    Three scenarios are covered in a single migration pass:
    - user with only a primary phonenumber
    - user with primary and alternative phonenumber
    - user with no phonenumber
    """

    app = "accounts"
    migrate_from = "0094_add_digitaladdress_and_preferred_address"
    migrate_to = "0095_remove_phonenumber_backfill_digital_addresses"

    def setUpBeforeMigration(self, apps):
        User = apps.get_model("accounts", "User")

        primary_only = User.objects.create(
            email="primary@example.com",
            phonenumber="0612345678",
        )
        self.primary_only_pk = primary_only.pk

        both = User.objects.create(
            email="both@example.com",
            phonenumber="0612345678",
            phonenumber_alternative="0687654321",
        )
        self.both_pk = both.pk

        no_phone = User.objects.create(email="nophone@example.com")
        self.no_phone_pk = no_phone.pk

    def test_primary_only_gets_single_standard_address(self):
        DigitalAddress = self.apps.get_model("accounts", "DigitalAddress")
        addresses = DigitalAddress.objects.filter(
            user_id=self.primary_only_pk, type="phone"
        )
        self.assertEqual(addresses.count(), 1)
        self.assertEqual(addresses.get().value, "0612345678")
        self.assertTrue(addresses.get().is_standard_for_type)

    def test_both_numbers_get_two_addresses(self):
        DigitalAddress = self.apps.get_model("accounts", "DigitalAddress")
        addresses = DigitalAddress.objects.filter(user_id=self.both_pk, type="phone")
        self.assertEqual(addresses.count(), 2)

    def test_primary_is_standard(self):
        DigitalAddress = self.apps.get_model("accounts", "DigitalAddress")
        standard = DigitalAddress.objects.get(
            user_id=self.both_pk, type="phone", is_standard_for_type=True
        )
        self.assertEqual(standard.value, "0612345678")

    def test_alternative_is_not_standard(self):
        DigitalAddress = self.apps.get_model("accounts", "DigitalAddress")
        alternative = DigitalAddress.objects.get(
            user_id=self.both_pk, type="phone", is_standard_for_type=False
        )
        self.assertEqual(alternative.value, "0687654321")

    def test_no_phone_gets_no_addresses(self):
        DigitalAddress = self.apps.get_model("accounts", "DigitalAddress")
        self.assertFalse(
            DigitalAddress.objects.filter(
                user_id=self.no_phone_pk, type="phone"
            ).exists()
        )
