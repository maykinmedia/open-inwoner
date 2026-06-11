from django.test import TestCase

from open_inwoner.accounts.choices import DigitalAddressType, LoginTypeChoices
from open_inwoner.accounts.models import DigitalAddress

from .factories import DigidUserFactory, UserFactory


def _addresses(user, type=None):
    qs = DigitalAddress.objects.filter(user=user)
    if type:
        qs = qs.filter(type=type)
    return list(qs.order_by("type", "value").values("type", "value", "login_type"))


class UserSaveCreatesSyncTests(TestCase):
    def test_new_user_creates_email_address(self):
        user = UserFactory(email="new@example.com", phonenumber="")

        self.assertEqual(
            _addresses(user, type=DigitalAddressType.email),
            [
                {
                    "type": DigitalAddressType.email,
                    "value": "new@example.com",
                    "login_type": LoginTypeChoices.default,
                }
            ],
        )

    def test_new_user_with_phone_creates_phone_address(self):
        user = UserFactory(email="new@example.com", phonenumber="0612345678")

        self.assertEqual(
            _addresses(user, type=DigitalAddressType.phone),
            [
                {
                    "type": DigitalAddressType.phone,
                    "value": "0612345678",
                    "login_type": LoginTypeChoices.default,
                }
            ],
        )

    def test_new_user_without_phone_creates_no_phone_address(self):
        user = UserFactory(phonenumber="")

        self.assertEqual(_addresses(user, type=DigitalAddressType.phone), [])

    def test_new_digid_user_address_carries_digid_login_type(self):
        user = DigidUserFactory(phonenumber="")

        self.assertEqual(
            _addresses(user, type=DigitalAddressType.email),
            [
                {
                    "type": DigitalAddressType.email,
                    "value": user.email,
                    "login_type": LoginTypeChoices.digid,
                }
            ],
        )


class UserSaveUpdatesSyncTests(TestCase):
    def test_email_change_updates_digital_address(self):
        user = UserFactory(email="old@example.com", phonenumber="")

        user.email = "new@example.com"
        user.save()

        self.assertEqual(
            _addresses(user, type=DigitalAddressType.email),
            [
                {
                    "type": DigitalAddressType.email,
                    "value": "new@example.com",
                    "login_type": LoginTypeChoices.default,
                }
            ],
        )

    def test_email_change_does_not_create_duplicate_address(self):
        user = UserFactory(email="old@example.com", phonenumber="")

        user.email = "new@example.com"
        user.save()

        self.assertEqual(
            DigitalAddress.objects.filter(
                user=user, type=DigitalAddressType.email
            ).count(),
            1,
        )

    def test_phone_change_updates_digital_address(self):
        user = UserFactory(phonenumber="0612345678")

        user.phonenumber = "0687654321"
        user.save()

        self.assertEqual(
            _addresses(user, type=DigitalAddressType.phone),
            [
                {
                    "type": DigitalAddressType.phone,
                    "value": "0687654321",
                    "login_type": LoginTypeChoices.default,
                }
            ],
        )

    def test_phone_set_from_empty_creates_new_address(self):
        user = UserFactory(phonenumber="")

        user.phonenumber = "0612345678"
        user.save()

        self.assertEqual(
            _addresses(user, type=DigitalAddressType.phone),
            [
                {
                    "type": DigitalAddressType.phone,
                    "value": "0612345678",
                    "login_type": LoginTypeChoices.default,
                }
            ],
        )

    def test_update_fields_email_syncs_email_address(self):
        user = UserFactory(email="old@example.com", phonenumber="")

        user.email = "new@example.com"
        user.save(update_fields=["email"])

        self.assertEqual(
            _addresses(user, type=DigitalAddressType.email),
            [
                {
                    "type": DigitalAddressType.email,
                    "value": "new@example.com",
                    "login_type": LoginTypeChoices.default,
                }
            ],
        )

    def test_update_fields_without_email_does_not_sync_email(self):
        user = UserFactory(email="old@example.com", phonenumber="")
        addr = DigitalAddress.objects.get(user=user, type=DigitalAddressType.email)
        original_value = addr.value

        # Change email in memory but save only a different field
        user.email = "new@example.com"
        user.save(update_fields=["first_name"])

        addr.refresh_from_db()
        self.assertEqual(addr.value, original_value)

    def test_digid_placeholder_to_real_email_updates_address(self):
        user = DigidUserFactory(phonenumber="")
        # Simulate NecessaryUserForm replacing the placeholder email
        user.email = "real@example.com"
        user.save()

        self.assertEqual(
            _addresses(user, type=DigitalAddressType.email),
            [
                {
                    "type": DigitalAddressType.email,
                    "value": "real@example.com",
                    "login_type": LoginTypeChoices.digid,
                }
            ],
        )
