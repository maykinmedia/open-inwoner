from django.test import tag

from open_inwoner.utils.tests.test_migrations import TestSuccessfulMigrations


@tag("migrations")
class BackfillDigitalAddressTests(TestSuccessfulMigrations):
    """
    Migration 0094 creates DigitalAddress rows from the existing flat fields
    email, phonenumber, and phonenumber_alternative on User.
    """

    app = "accounts"
    migrate_from = "0093_add_digitaladdress_and_preferred_address"
    migrate_to = "0094_backfill_digitaladdress_from_user_flat_fields"

    def setUpBeforeMigration(self, apps):
        User = apps.get_model("accounts", "User")

        self.email_only_user = User.objects.create(
            email="email-only@example.com",
            phonenumber="",
            phonenumber_alternative="",
            login_type="default",
        )
        self.user_with_phone = User.objects.create(
            email="with-phone@example.com",
            phonenumber="0612345678",
            phonenumber_alternative="",
            login_type="default",
        )
        self.user_with_both_phones = User.objects.create(
            email="both-phones@example.com",
            phonenumber="0612345678",
            phonenumber_alternative="0687654321",
            login_type="default",
        )
        self.digid_user = User.objects.create(
            email="abc123@localhost",
            phonenumber="",
            phonenumber_alternative="",
            login_type="digid",
        )

    def _addresses_for(self, user_id):
        DigitalAddress = self.apps.get_model("accounts", "DigitalAddress")
        return list(
            DigitalAddress.objects.filter(user_id=user_id)
            .order_by("type", "value")
            .values("type", "value", "login_type")
        )

    def _preferred_address_for(self, user_id):
        User = self.apps.get_model("accounts", "User")
        DigitalAddress = self.apps.get_model("accounts", "DigitalAddress")
        user = User.objects.get(pk=user_id)
        if user.preferred_address_id is None:
            return None
        return (
            DigitalAddress.objects.filter(pk=user.preferred_address_id)
            .values("type", "value")
            .get()
        )

    def test_email_only_user_gets_one_email_address(self):
        self.assertEqual(
            self._addresses_for(self.email_only_user.pk),
            [
                {
                    "type": "email",
                    "value": "email-only@example.com",
                    "login_type": "default",
                }
            ],
        )

    def test_user_with_primary_phone_gets_email_and_phone(self):
        self.assertEqual(
            self._addresses_for(self.user_with_phone.pk),
            [
                {
                    "type": "email",
                    "value": "with-phone@example.com",
                    "login_type": "default",
                },
                {"type": "phone", "value": "0612345678", "login_type": "default"},
            ],
        )

    def test_user_with_both_phones_gets_three_addresses(self):
        self.assertEqual(
            self._addresses_for(self.user_with_both_phones.pk),
            [
                {
                    "type": "email",
                    "value": "both-phones@example.com",
                    "login_type": "default",
                },
                {"type": "phone", "value": "0612345678", "login_type": "default"},
                {"type": "phone", "value": "0687654321", "login_type": "default"},
            ],
        )

    def test_digid_user_address_carries_digid_login_type(self):
        self.assertEqual(
            self._addresses_for(self.digid_user.pk),
            [{"type": "email", "value": "abc123@localhost", "login_type": "digid"}],
        )

    def test_preferred_address_is_set_to_email_address(self):
        self.assertEqual(
            self._preferred_address_for(self.email_only_user.pk),
            {"type": "email", "value": "email-only@example.com"},
        )

    def test_preferred_address_is_set_for_user_with_phone(self):
        self.assertEqual(
            self._preferred_address_for(self.user_with_phone.pk),
            {"type": "email", "value": "with-phone@example.com"},
        )

    def test_preferred_address_is_set_for_digid_user(self):
        self.assertEqual(
            self._preferred_address_for(self.digid_user.pk),
            {"type": "email", "value": "abc123@localhost"},
        )
