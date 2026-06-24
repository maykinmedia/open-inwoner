from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from open_inwoner.accounts.choices import DigitalAddressType, LoginTypeChoices
from open_inwoner.accounts.models import DigitalAddress

from .factories import DigidUserFactory, DigitalAddressFactory, UserFactory


class DigitalAddressModelTests(TestCase):
    def test_str(self):
        addr = DigitalAddressFactory.build(
            type=DigitalAddressType.email, value="test@example.com"
        )
        self.assertEqual(str(addr), "E-mailadres: test@example.com")

    def test_create_email_address(self):
        addr = DigitalAddressFactory(
            type=DigitalAddressType.email, value="test@example.com"
        )
        self.assertEqual(addr.type, DigitalAddressType.email)
        self.assertEqual(addr.value, "test@example.com")
        self.assertIsNotNone(addr.created_at)

    def test_create_phone_address(self):
        addr = DigitalAddressFactory(type=DigitalAddressType.phone, value="0612345678")
        self.assertEqual(addr.type, DigitalAddressType.phone)

    def test_cascade_delete_with_user(self):
        addr = DigitalAddressFactory()
        addr_pk = addr.pk
        addr.user.delete()
        self.assertFalse(DigitalAddress.objects.filter(pk=addr_pk).exists())


class DigitalAddressValueValidationTests(TestCase):
    def test_clean_rejects_invalid_email(self):
        addr = DigitalAddressFactory.build(
            type=DigitalAddressType.email, value="not-an-email"
        )
        with self.assertRaises(ValidationError) as ctx:
            addr.clean()

        self.assertEqual(
            ctx.exception.message_dict, {"value": ["Voer een geldig e-mailadres in."]}
        )

    def test_clean_rejects_invalid_phone(self):
        addr = DigitalAddressFactory.build(
            type=DigitalAddressType.phone, value="not-a-phone"
        )
        with self.assertRaises(ValidationError) as ctx:
            addr.clean()

        self.assertEqual(
            ctx.exception.message_dict, {"value": ["Enter a valid phone number."]}
        )

    def test_clean_accepts_valid_email(self):
        addr = DigitalAddressFactory.build(
            type=DigitalAddressType.email, value="valid@example.com"
        )
        addr.clean()  # should not raise

    def test_clean_accepts_valid_dutch_phone(self):
        addr = DigitalAddressFactory.build(
            type=DigitalAddressType.phone, value="0612345678"
        )
        addr.clean()  # should not raise


class DigitalAddressUniqueConstraintTests(TestCase):
    def test_unique_constraint_prevents_duplicate_email_for_regular_users(self):
        DigitalAddressFactory(
            type=DigitalAddressType.email,
            value="shared@example.com",
            login_type=LoginTypeChoices.default,
        )
        with self.assertRaises(IntegrityError):
            DigitalAddressFactory(
                type=DigitalAddressType.email,
                value="shared@example.com",
                login_type=LoginTypeChoices.default,
            )

    def test_unique_constraint_allows_duplicate_email_for_different_digid_users(self):
        DigitalAddressFactory(
            user=DigidUserFactory(),
            type=DigitalAddressType.email,
            value="shared@example.com",
            login_type=LoginTypeChoices.digid,
        )
        addr = DigitalAddressFactory(
            user=DigidUserFactory(),
            type=DigitalAddressType.email,
            value="shared@example.com",
            login_type=LoginTypeChoices.digid,
        )
        self.assertIsNotNone(addr.pk)

    def test_unique_constraint_does_not_apply_to_phone(self):
        DigitalAddressFactory(type=DigitalAddressType.phone, value="0612345678")
        addr = DigitalAddressFactory(type=DigitalAddressType.phone, value="0612345678")
        self.assertIsNotNone(addr.pk)

    def test_unique_constraint_prevents_duplicate_per_user_type_value(self):
        existing = DigitalAddressFactory(
            type=DigitalAddressType.email, value="test@example.com"
        )
        with self.assertRaises(IntegrityError):
            DigitalAddressFactory(
                user=existing.user,
                type=DigitalAddressType.email,
                value="test@example.com",
                login_type=LoginTypeChoices.digid,
            )

    def test_unique_constraint_allows_same_value_different_user(self):
        DigitalAddressFactory(
            user=DigidUserFactory(),
            type=DigitalAddressType.email,
            value="same@example.com",
            login_type=LoginTypeChoices.digid,
        )
        addr = DigitalAddressFactory(
            user=DigidUserFactory(),
            type=DigitalAddressType.email,
            value="same@example.com",
            login_type=LoginTypeChoices.digid,
        )
        self.assertIsNotNone(addr.pk)

    def test_unique_constraint_allows_same_value_different_type(self):
        existing = DigitalAddressFactory(
            type=DigitalAddressType.email, value="test@example.com"
        )
        addr = DigitalAddressFactory(
            user=existing.user,
            type=DigitalAddressType.phone,
            value="test@example.com",
        )
        self.assertIsNotNone(addr.pk)


class PreferredAddressTests(TestCase):
    def test_preferred_address_set_null_on_address_delete(self):
        addr = DigitalAddressFactory()
        addr.user.preferred_address = addr
        addr.user.save()

        addr.delete()
        addr.user.refresh_from_db()
        self.assertIsNone(addr.user.preferred_address)

    def test_preferred_address_defaults_to_null(self):
        user = UserFactory()
        self.assertIsNone(user.preferred_address)

    def test_clean_rejects_preferred_address_belonging_to_other_user(self):
        user1 = UserFactory()
        addr = DigitalAddressFactory(user=UserFactory())
        user1.preferred_address = addr
        with self.assertRaises(ValidationError) as ctx:
            user1.clean()
        self.assertEqual(
            ctx.exception.message_dict,
            {"preferred_address": ["The preferred address must belong to this user."]},
        )

    def test_clean_allows_preferred_address_belonging_to_same_user(self):
        addr = DigitalAddressFactory()
        addr.user.preferred_address = addr
        addr.user.clean()  # should not raise


class DigitalAddressIsStandardTests(TestCase):
    def test_is_standard_for_type_defaults_to_false(self):
        addr = DigitalAddressFactory()
        self.assertFalse(addr.is_standard_for_type)

    def test_can_set_one_standard_per_user_type(self):
        addr = DigitalAddressFactory(is_standard_for_type=True)
        self.assertTrue(addr.is_standard_for_type)

    def test_unique_constraint_prevents_two_standards_same_user_type(self):
        existing = DigitalAddressFactory(
            type=DigitalAddressType.email,
            is_standard_for_type=True,
        )
        with self.assertRaises(IntegrityError):
            DigitalAddressFactory(
                user=existing.user,
                type=DigitalAddressType.email,
                value="other@example.com",
                is_standard_for_type=True,
            )

    def test_unique_constraint_allows_standard_per_different_type(self):
        user_addr = DigitalAddressFactory(
            type=DigitalAddressType.email,
            is_standard_for_type=True,
        )
        phone_addr = DigitalAddressFactory(
            user=user_addr.user,
            type=DigitalAddressType.phone,
            value="0612345678",
            is_standard_for_type=True,
        )
        self.assertTrue(phone_addr.is_standard_for_type)

    def test_unique_constraint_allows_standard_per_different_user(self):
        DigitalAddressFactory(
            type=DigitalAddressType.email,
            is_standard_for_type=True,
        )
        addr = DigitalAddressFactory(
            type=DigitalAddressType.email,
            value="other@example.com",
            is_standard_for_type=True,
        )
        self.assertTrue(addr.is_standard_for_type)

    def test_unique_constraint_allows_multiple_non_standard_same_user_type(self):
        existing = DigitalAddressFactory(
            type=DigitalAddressType.email,
            is_standard_for_type=False,
        )
        addr = DigitalAddressFactory(
            user=existing.user,
            type=DigitalAddressType.email,
            value="second@example.com",
            is_standard_for_type=False,
        )
        self.assertIsNotNone(addr.pk)


class DigitalAddressOrderingTests(TestCase):
    def test_standard_address_is_first(self):
        user = UserFactory()
        alt = DigitalAddressFactory(
            user=user,
            type=DigitalAddressType.email,
            value="alt@example.com",
            is_standard_for_type=False,
        )
        standard = DigitalAddressFactory(
            user=user,
            type=DigitalAddressType.email,
            value="standard@example.com",
            is_standard_for_type=True,
        )
        addresses = list(user.digital_addresses.filter(type=DigitalAddressType.email))
        self.assertEqual(addresses, [standard, alt])
