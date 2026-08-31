import datetime
from unittest.mock import Mock, call, patch

from django.test import TestCase

from open_inwoner.accounts.choices import DigitalAddressType
from open_inwoner.accounts.models import DigitalAddress
from open_inwoner.accounts.tests.factories import (
    DigidUserFactory,
    DigitalAddressFactory,
    UserFactory,
)
from open_inwoner.openklant.constants import Status
from open_inwoner.openklant.services import (
    OpenKlant2Answer,
    OpenKlant2Question,
    OpenKlant2Service,
    _normalize_email,
    _normalize_phone,
)
from open_inwoner.openklant.tests.factories import (
    DigitaalAdresOpenKlantMappingFactory,
    OpenKlant2ConfigFactory,
)
from open_inwoner.openklant.tests.test_conversations import (
    make_klantcontact,
    make_not_found,
)
from open_inwoner.utils.test import ClearCachesMixin


@patch("open_inwoner.openklant.services.OpenKlantClient")
class UpdateUserFromPartijTestCase(TestCase):
    PARTIJ_UUID = "partij-uuid-1234"

    def setUp(self):
        self.config = OpenKlant2ConfigFactory()

    def _make_adres(self, uuid, soort, adres, is_standaard=False):
        return {
            "uuid": uuid,
            "soortDigitaalAdres": soort,
            "adres": adres,
            "isStandaardAdres": is_standaard,
            "omschrijving": "",
            "verstrektDoorPartij": {"uuid": self.PARTIJ_UUID},
            "verstrektDoorBetrokkene": None,
        }

    def _list_response(self, results):
        return {
            "count": len(results),
            "next": None,
            "previous": None,
            "results": results,
        }

    def _partij(self, voorkeurs_uuid=None):
        return {
            "uuid": self.PARTIJ_UUID,
            "voorkeursDigitaalAdres": (
                {"uuid": voorkeurs_uuid} if voorkeurs_uuid else None
            ),
        }

    def test_known_uuid_updates_local_value(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.digitaal_adres.list.return_value = self._list_response(
            [
                self._make_adres(
                    "11111111-1111-1111-1111-111111111111",
                    "email",
                    "updated@example.com",
                )
            ]
        )

        user = DigidUserFactory()
        address = DigitalAddressFactory(
            user=user, type=DigitalAddressType.email, value="old@example.com"
        )
        DigitaalAdresOpenKlantMappingFactory(
            digital_address=address,
            ok_uuid="11111111-1111-1111-1111-111111111111",
        )

        service = OpenKlant2Service(config=self.config)
        service.update_user_from_partij(self._partij(), user)

        address.refresh_from_db()
        self.assertEqual(address.value, "updated@example.com")

    def test_unknown_uuid_creates_local_address_and_mapping(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.digitaal_adres.list.return_value = self._list_response(
            [
                self._make_adres(
                    "22222222-2222-2222-2222-222222222222",
                    "telefoonnummer",
                    "0612345678",
                )
            ]
        )

        user = DigidUserFactory()

        service = OpenKlant2Service(config=self.config)
        service.update_user_from_partij(self._partij(), user)

        address = user.digital_addresses.get(type=DigitalAddressType.phone)
        self.assertEqual(address.value, "0612345678")
        self.assertEqual(
            str(address.openklant_mapping.ok_uuid),
            "22222222-2222-2222-2222-222222222222",
        )

    def test_stale_mapping_deletes_local_address(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.digitaal_adres.list.return_value = self._list_response([])

        user = DigidUserFactory()
        address = DigitalAddressFactory(
            user=user, type=DigitalAddressType.phone, value="0612345678"
        )
        DigitaalAdresOpenKlantMappingFactory(
            digital_address=address,
            ok_uuid="33333333-3333-3333-3333-333333333333",
        )

        service = OpenKlant2Service(config=self.config)
        service.update_user_from_partij(self._partij(), user)

        self.assertFalse(DigitalAddress.objects.filter(pk=address.pk).exists())

    def test_user_email_not_cleared_when_stale_email_deleted(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.digitaal_adres.list.return_value = self._list_response([])
        new_remote_uuid = "dddddddd-dddd-dddd-dddd-dddddddddddd"
        mock_client.digitaal_adres.create.return_value = self._make_adres(
            new_remote_uuid, "email", "keep@example.com", is_standaard=True
        )

        user = DigidUserFactory(email="keep@example.com")
        address = DigitalAddressFactory(
            user=user, type=DigitalAddressType.email, value="keep@example.com"
        )
        DigitaalAdresOpenKlantMappingFactory(
            digital_address=address,
            ok_uuid="44444444-4444-4444-4444-444444444444",
        )

        service = OpenKlant2Service(config=self.config)
        result = service.update_user_from_partij(self._partij(), user)

        user.refresh_from_db()
        self.assertEqual(user.email, "keep@example.com")
        self.assertEqual(result.orphaned_addresses_restored, 1)

    def test_orphaned_restore_does_not_duplicate_new_remote_standard(
        self, mock_client_class
    ):
        """
        Regression test for #2793: if the DA backing the old standard email
        is deleted (its UUID vanished from the remote list) in the same sync
        run where remote designates a *different* address as the new
        standard, the orphan-restore step must not also mark the recreated
        old value as standard -- that would create two
        is_standard_for_type=True rows for (user, email) and violate
        unique_standard_digital_address_per_user_type.
        """
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        new_remote_uuid = "dddddddd-dddd-dddd-dddd-dddddddddddd"
        mock_client.digitaal_adres.list.return_value = self._list_response(
            [
                self._make_adres(
                    new_remote_uuid,
                    "email",
                    "new@example.com",
                    is_standaard=True,
                ),
            ]
        )

        user = DigidUserFactory(email="old@example.com")
        address = DigitalAddressFactory(
            user=user,
            type=DigitalAddressType.email,
            value="old@example.com",
            is_standard_for_type=True,
        )
        DigitaalAdresOpenKlantMappingFactory(
            digital_address=address,
            ok_uuid="44444444-4444-4444-4444-444444444444",
        )

        service = OpenKlant2Service(config=self.config)
        result = service.update_user_from_partij(self._partij(), user)

        user.refresh_from_db()
        self.assertEqual(user.email, "new@example.com")
        self.assertEqual(result.orphaned_addresses_restored, 0)

        standard_addresses = user.digital_addresses.filter(
            type=DigitalAddressType.email, is_standard_for_type=True
        )
        self.assertEqual(standard_addresses.count(), 1)
        self.assertEqual(standard_addresses.get().value, "new@example.com")

    def test_orphaned_restore_runs_when_remote_standard_is_owned_by_other_user(
        self, mock_client_class
    ):
        """
        Regression test for #2793 (PR follow-up): remote can designate a
        standard address that isn't actually applied locally -- e.g. because
        it's an email already owned by a different user, so Phase 1 skips
        creating it and it's never added to local_by_uuid. Phase 2/3 then
        correctly no-op for that type (nothing local to promote/sync to), but
        the orphan-restore guard must not mistake remote_standard_uuid_by_type
        being non-None for "already handled" -- it must still restore the
        dangling flat value, since nothing else did.
        """
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Another user already owns the address remote wants to promote.
        UserFactory(email="shared@example.com")

        shared_remote_uuid = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"
        mock_client.digitaal_adres.list.return_value = self._list_response(
            [
                self._make_adres(
                    shared_remote_uuid,
                    "email",
                    "shared@example.com",
                    is_standaard=True,
                ),
            ]
        )

        user = DigidUserFactory(email="old@example.com")
        address = DigitalAddressFactory(
            user=user,
            type=DigitalAddressType.email,
            value="old@example.com",
            is_standard_for_type=True,
        )
        DigitaalAdresOpenKlantMappingFactory(
            digital_address=address,
            ok_uuid="99999999-9999-9999-9999-999999999999",
        )

        service = OpenKlant2Service(config=self.config)
        result = service.update_user_from_partij(self._partij(), user)

        user.refresh_from_db()
        self.assertEqual(result.email_conflicts_skipped, 1)
        self.assertEqual(user.email, "old@example.com")
        self.assertEqual(result.orphaned_addresses_restored, 1)

        standard_addresses = user.digital_addresses.filter(
            type=DigitalAddressType.email, is_standard_for_type=True
        )
        self.assertEqual(standard_addresses.count(), 1)
        self.assertEqual(standard_addresses.get().value, "old@example.com")

    def test_email_conflict_with_other_user_is_skipped(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Another user already owns this email address
        UserFactory(email="taken@example.com")

        mock_client.digitaal_adres.list.return_value = self._list_response(
            [
                self._make_adres(
                    "55555555-5555-5555-5555-555555555555",
                    "email",
                    "taken@example.com",
                )
            ]
        )

        user = DigidUserFactory()

        service = OpenKlant2Service(config=self.config)
        result = service.update_user_from_partij(self._partij(), user)

        self.assertFalse(user.digital_addresses.exists())
        self.assertEqual(result.email_conflicts_skipped, 1)

    def test_standard_remote_address_sets_local_standard_flag_and_flat_field(
        self, mock_client_class
    ):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.digitaal_adres.list.return_value = self._list_response(
            [
                self._make_adres(
                    "66666666-6666-6666-6666-666666666666",
                    "telefoonnummer",
                    "0612345678",
                    is_standaard=True,
                ),
                self._make_adres(
                    "77777777-7777-7777-7777-777777777777",
                    "telefoonnummer",
                    "0687654321",
                    is_standaard=False,
                ),
            ]
        )

        user = DigidUserFactory(phonenumber="")

        service = OpenKlant2Service(config=self.config)
        service.update_user_from_partij(self._partij(), user)

        standard = user.digital_addresses.get(value="0612345678")
        alternative = user.digital_addresses.get(value="0687654321")
        self.assertTrue(standard.is_standard_for_type)
        self.assertFalse(alternative.is_standard_for_type)

        user.refresh_from_db()
        self.assertEqual(user.phonenumber, "0612345678")

    def test_local_standard_preserved_when_remote_has_no_standard(
        self, mock_client_class
    ):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.digitaal_adres.list.return_value = self._list_response(
            [
                self._make_adres(
                    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                    "telefoonnummer",
                    "0612345678",
                    is_standaard=False,
                ),
            ]
        )

        user = DigidUserFactory(phonenumber="0612345678")
        address = DigitalAddressFactory(
            user=user,
            type=DigitalAddressType.phone,
            value="0612345678",
            is_standard_for_type=True,
        )
        DigitaalAdresOpenKlantMappingFactory(
            digital_address=address,
            ok_uuid="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        )

        service = OpenKlant2Service(config=self.config)
        service.update_user_from_partij(self._partij(), user)

        address.refresh_from_db()
        self.assertTrue(address.is_standard_for_type)

    def test_push_back_standard_email_when_remote_has_no_addresses(
        self, mock_client_class
    ):
        """When remote has no addresses at all, push the local standard email as default."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.digitaal_adres.list.return_value = self._list_response([])
        new_remote_uuid = "dddddddd-dddd-dddd-dddd-dddddddddddd"
        mock_client.digitaal_adres.create.return_value = self._make_adres(
            new_remote_uuid, "email", "user@example.com", is_standaard=True
        )

        user = DigidUserFactory(email="user@example.com")
        local_email_da = DigitalAddressFactory(
            user=user,
            type=DigitalAddressType.email,
            value="user@example.com",
            is_standard_for_type=True,
        )

        service = OpenKlant2Service(config=self.config)
        service.update_user_from_partij(self._partij(), user)

        mock_client.digitaal_adres.create.assert_called_once()
        mapping = local_email_da.openklant_mapping
        self.assertEqual(str(mapping.ok_uuid), new_remote_uuid)

    def test_push_back_standard_email_when_remote_has_no_email_addresses(
        self, mock_client_class
    ):
        """When remote has no email addresses (only other types), push the local standard email."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.digitaal_adres.list.return_value = self._list_response(
            [
                self._make_adres(
                    "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                    "telefoonnummer",
                    "0612345678",
                    is_standaard=True,
                ),
            ]
        )
        new_remote_uuid = "dddddddd-dddd-dddd-dddd-dddddddddddd"
        mock_client.digitaal_adres.create.return_value = self._make_adres(
            new_remote_uuid, "email", "user@example.com", is_standaard=True
        )

        user = DigidUserFactory(email="user@example.com")
        local_email_da = DigitalAddressFactory(
            user=user,
            type=DigitalAddressType.email,
            value="user@example.com",
            is_standard_for_type=True,
        )

        service = OpenKlant2Service(config=self.config)
        service.update_user_from_partij(self._partij(), user)

        mock_client.digitaal_adres.create.assert_called_once()
        mapping = local_email_da.openklant_mapping
        self.assertEqual(str(mapping.ok_uuid), new_remote_uuid)

    def test_push_back_standard_email_when_remote_email_has_no_standard(
        self, mock_client_class
    ):
        """When remote has email addresses but none is standard, push ours."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        non_standard_uuid = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        mock_client.digitaal_adres.list.return_value = self._list_response(
            [
                self._make_adres(
                    non_standard_uuid,
                    "email",
                    "other@example.com",
                    is_standaard=False,
                ),
            ]
        )
        new_remote_uuid = "dddddddd-dddd-dddd-dddd-dddddddddddd"
        mock_client.digitaal_adres.create.return_value = self._make_adres(
            new_remote_uuid, "email", "user@example.com", is_standaard=True
        )

        user = DigidUserFactory(email="user@example.com")
        local_email_da = DigitalAddressFactory(
            user=user,
            type=DigitalAddressType.email,
            value="user@example.com",
            is_standard_for_type=True,
        )

        service = OpenKlant2Service(config=self.config)
        service.update_user_from_partij(self._partij(), user)

        mock_client.digitaal_adres.create.assert_called_once()
        mapping = local_email_da.openklant_mapping
        self.assertEqual(str(mapping.ok_uuid), new_remote_uuid)

    def test_voorkeurs_digitaal_adres_sets_preferred_address(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.digitaal_adres.list.return_value = self._list_response(
            [
                self._make_adres(
                    "88888888-8888-8888-8888-888888888888",
                    "email",
                    "preferred@example.com",
                )
            ]
        )

        user = DigidUserFactory()

        service = OpenKlant2Service(config=self.config)
        service.update_user_from_partij(
            self._partij(voorkeurs_uuid="88888888-8888-8888-8888-888888888888"),
            user,
        )

        user.refresh_from_db()
        self.assertEqual(user.preferred_address.value, "preferred@example.com")

    def test_preferred_address_cleared_when_remote_has_no_preference(
        self, mock_client_class
    ):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.digitaal_adres.list.return_value = self._list_response(
            [
                self._make_adres(
                    "99999999-9999-9999-9999-999999999999",
                    "email",
                    "kept@example.com",
                )
            ]
        )

        user = DigidUserFactory()
        address = DigitalAddressFactory(
            user=user, type=DigitalAddressType.email, value="kept@example.com"
        )
        DigitaalAdresOpenKlantMappingFactory(
            digital_address=address,
            ok_uuid="99999999-9999-9999-9999-999999999999",
        )
        user.preferred_address = address
        user.save(update_fields=["preferred_address"])

        service = OpenKlant2Service(config=self.config)
        service.update_user_from_partij(self._partij(), user)

        user.refresh_from_db()
        self.assertIsNone(user.preferred_address)


@patch("open_inwoner.openklant.services.OpenKlantClient")
class CreateKlantcontactTestCase(TestCase):
    def setUp(self):
        self.config = OpenKlant2ConfigFactory()

    def test_raises_error_when_question_is_empty(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        service = OpenKlant2Service(config=self.config)

        for empty_question in ["", "   ", "\n", "  \n  "]:
            with self.subTest(question=repr(empty_question)):
                with self.assertRaises(ValueError) as cm:
                    service._create_klantcontact(
                        question=empty_question, subject="Test subject"
                    )

                self.assertIn("must provide a question", str(cm.exception))

    def test_raises_error_when_actor_not_configured(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Use existing config but override actor
        service = OpenKlant2Service(config=self.config)
        service.config.mijn_vragen_actor = None

        with self.assertRaises(RuntimeError) as cm:
            service._create_klantcontact(question="Valid question", subject="Subject")

        self.assertIn("must define an actor", str(cm.exception))

    def test_creates_klantcontact_with_valid_data(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_client.klant_contact.create.return_value = {
            "uuid": "kc-uuid",
            "inhoud": "My question",
            "onderwerp": "Subject",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
        }

        service = OpenKlant2Service(config=self.config)
        result = service._create_klantcontact(question="My question", subject="Subject")

        # Verify client was called correctly
        mock_client.klant_contact.create.assert_called_once()
        call_data = mock_client.klant_contact.create.call_args[1]["data"]

        self.assertEqual(call_data["inhoud"], "My question")
        self.assertEqual(call_data["onderwerp"], "Subject")
        self.assertEqual(call_data["kanaal"], self.config.mijn_vragen_kanaal)
        self.assertEqual(call_data["taal"], "nld")

        # Verify return value
        self.assertEqual(result["uuid"], "kc-uuid")


@patch("open_inwoner.openklant.services.OpenKlantClient")
class GetOrCreatePartijForUserTestCase(TestCase):
    def setUp(self):
        self.config = OpenKlant2ConfigFactory()

    def test_find_existing_persoon_by_bsn(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # The listing returns the full partij representation, which is why the
        # lookup does not retrieve it again.
        mock_client.partij.list.return_value = {
            "count": 1,
            "results": [
                {
                    "uuid": "existing-uuid",
                    "soortPartij": "persoon",
                    "partijIdentificatie": {
                        "contactnaam": {"voornaam": "John", "achternaam": "Doe"}
                    },
                }
            ],
        }

        service = OpenKlant2Service(config=self.config)
        user = DigidUserFactory(bsn="123456789")

        partij, created = service.get_or_create_partij_for_user(user)

        self.assertFalse(created, "Should retrieve existing partij, not create new")
        self.assertEqual(partij["uuid"], "existing-uuid")
        self.assertEqual(
            partij["partijIdentificatie"]["contactnaam"]["voornaam"], "John"
        )
        mock_client.partij.retrieve.assert_not_called()

        # Verify searched by BSN
        mock_client.partij.list.assert_called_once()
        call_params = mock_client.partij.list.call_args[1]["params"]
        self.assertEqual(call_params["partijIdentificator__objectId"], "123456789")
        self.assertEqual(call_params["partijIdentificator__codeSoortObjectId"], "bsn")

    def test_create_new_persoon_when_not_found(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_client.partij.list.return_value = {"count": 0, "results": []}

        mock_client.partij.create_persoon.return_value = {
            "uuid": "new-uuid",
            "soortPartij": "persoon",
            "partijIdentificatie": {
                "contactnaam": {"voornaam": "Jane", "achternaam": "Smith"}
            },
        }

        service = OpenKlant2Service(config=self.config)
        user = DigidUserFactory(first_name="Jane", last_name="Smith", bsn="987654321")

        partij, created = service.get_or_create_partij_for_user(user)

        self.assertTrue(created, "Should create new partij")
        self.assertEqual(partij["uuid"], "new-uuid")

        # Verify creation data includes BSN
        mock_client.partij.create_persoon.assert_called_once()
        call_data = mock_client.partij.create_persoon.call_args[1]["data"]
        self.assertEqual(call_data["soortPartij"], "persoon")
        self.assertEqual(
            call_data["partijIdentificatie"]["contactnaam"]["voornaam"], "Jane"
        )
        self.assertEqual(
            call_data["partijIdentificatie"]["contactnaam"]["achternaam"], "Smith"
        )
        self.assertIn("partijIdentificatoren", call_data)
        self.assertEqual(
            call_data["partijIdentificatoren"][0]["partijIdentificator"]["objectId"],
            "987654321",
        )

    def test_create_persoon_without_identificatoren_when_no_bsn(
        self, mock_client_class
    ):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_client.partij.list.return_value = {"count": 0, "results": []}
        mock_client.partij.create_persoon.return_value = {
            "uuid": "no-bsn-uuid",
            "soortPartij": "persoon",
            "partijIdentificatie": {
                "contactnaam": {"voornaam": "Anonymous", "achternaam": "User"}
            },
        }

        service = OpenKlant2Service(config=self.config)
        user = UserFactory(first_name="Anonymous", last_name="User", bsn="", kvk="")

        partij, created = service.get_or_create_partij_for_user(user)

        self.assertTrue(created)
        self.assertEqual(partij["uuid"], "no-bsn-uuid")

        # Verify NO identificatoren in the creation data
        call_data = mock_client.partij.create_persoon.call_args[1]["data"]
        self.assertNotIn(
            "partijIdentificatoren",
            call_data,
            "Should not include identificatoren when user has no BSN",
        )


@patch("open_inwoner.openklant.services.OpenKlantClient")
class FindPartijForParamsTestCase(TestCase):
    def setUp(self):
        self.config = OpenKlant2ConfigFactory()

    def test_partij_is_taken_from_the_listing_without_a_second_request(
        self, mock_client_class
    ):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.partij.list.return_value = {
            "count": 1,
            "results": [{"uuid": "partij-uuid", "soortPartij": "persoon"}],
        }

        service = OpenKlant2Service(config=self.config)

        partij = service.find_persoon_for_bsn("123456789")

        self.assertEqual(partij, {"uuid": "partij-uuid", "soortPartij": "persoon"})
        self.assertEqual(mock_client.partij.list.call_count, 1)
        mock_client.partij.retrieve.assert_not_called()

    def test_returns_none_when_no_partij_matches(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.partij.list.return_value = {"count": 0, "results": []}

        service = OpenKlant2Service(config=self.config)

        self.assertIsNone(service.find_persoon_for_bsn("123456789"))
        mock_client.partij.retrieve.assert_not_called()

    def test_first_partij_is_used_when_several_match(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.partij.list.return_value = {
            "count": 2,
            "results": [{"uuid": "first-uuid"}, {"uuid": "second-uuid"}],
        }

        service = OpenKlant2Service(config=self.config)

        with self.assertLogs("open_inwoner.openklant.services", level="ERROR"):
            partij = service.find_persoon_for_bsn("123456789")

        self.assertEqual(partij["uuid"], "first-uuid")


@patch("open_inwoner.openklant.services.OpenKlantClient")
class ResolvePartijUuidTestCase(ClearCachesMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.config = OpenKlant2ConfigFactory()

    def _mock_client(self, mock_client_class, uuid="partij-uuid"):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.partij.list.return_value = {
            "count": 1,
            "results": [{"uuid": uuid}],
        }
        return mock_client

    def _resolve(self, user):
        service = OpenKlant2Service(config=self.config)
        return service.resolve_partij_uuid(
            user, lambda: service.get_partij_for_user(user)
        )

    def test_second_lookup_is_served_from_cache(self, mock_client_class):
        mock_client = self._mock_client(mock_client_class)
        user = DigidUserFactory(bsn="123456789")

        self.assertEqual(self._resolve(user), "partij-uuid")
        self.assertEqual(self._resolve(user), "partij-uuid")

        self.assertEqual(mock_client.partij.list.call_count, 1)

    def test_lookup_is_repeated_when_caching_is_disabled(self, mock_client_class):
        mock_client = self._mock_client(mock_client_class)
        self.config.partij_cache_timeout = None
        self.config.save()
        user = DigidUserFactory(bsn="123456789")

        self.assertEqual(self._resolve(user), "partij-uuid")
        self.assertEqual(self._resolve(user), "partij-uuid")

        self.assertEqual(mock_client.partij.list.call_count, 2)

    def test_missing_partij_is_not_cached(self, mock_client_class):
        mock_client = self._mock_client(mock_client_class)
        mock_client.partij.list.return_value = {"count": 0, "results": []}
        user = DigidUserFactory(bsn="123456789")

        self.assertIsNone(self._resolve(user))

        mock_client.partij.list.return_value = {
            "count": 1,
            "results": [{"uuid": "created-later"}],
        }
        self.assertEqual(self._resolve(user), "created-later")

    def test_users_do_not_share_a_cache_entry(self, mock_client_class):
        mock_client = self._mock_client(mock_client_class, uuid="first-partij")
        first = DigidUserFactory(bsn="123456789")
        second = DigidUserFactory(bsn="987654321")

        self.assertEqual(self._resolve(first), "first-partij")

        mock_client.partij.list.return_value = {
            "count": 1,
            "results": [{"uuid": "second-partij"}],
        }
        self.assertEqual(self._resolve(second), "second-partij")

    def test_bsn_does_not_appear_in_the_cache_key(self, mock_client_class):
        self._mock_client(mock_client_class)
        user = DigidUserFactory(bsn="123456789")
        service = OpenKlant2Service(config=self.config)

        self.assertNotIn("123456789", service._partij_uuid_cache_key(user))


@patch("open_inwoner.openklant.services.OpenKlantClient")
class OpenKlant2QuestionAnswerTestCase(ClearCachesMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.config = OpenKlant2ConfigFactory()

    def test_answer_property_returns_none_when_no_answers(self, mock_client_class):
        question = OpenKlant2Question(
            url="http://example.com/question/1",
            question="What is the final answer?",
            question_kcm_uuid="q-uuid-1",
            onderwerp="Philosophy",
            kanaal="online",
            taal="nld",
            nummer="0001",
            plaatsgevonden_op=datetime.datetime(
                2024, 10, 2, 14, 0, 0, tzinfo=datetime.timezone.utc
            ),
            answers=[],
        )

        self.assertIsNone(question.answer)

    def test_answer_property_returns_newest(self, mock_client_class):
        """
        Verify that the field_validator automatically sorts answers by datetime (newest first).
        """
        answer_old = OpenKlant2Answer(
            answer="First answer",
            answer_kcm_uuid="a-uuid-1",
            nummer="0002",
            plaatsgevonden_op=datetime.datetime(
                2024, 10, 2, 14, 0, 0, tzinfo=datetime.timezone.utc
            ),
        )
        answer_middle = OpenKlant2Answer(
            answer="Updated answer",
            answer_kcm_uuid="a-uuid-2",
            nummer="0003",
            plaatsgevonden_op=datetime.datetime(
                2025, 10, 2, 14, 30, 0, tzinfo=datetime.timezone.utc
            ),
        )
        answer_new = OpenKlant2Answer(
            answer="Final answer",
            answer_kcm_uuid="a-uuid-3",
            nummer="0004",
            plaatsgevonden_op=datetime.datetime(
                2026, 10, 2, 15, 0, 0, tzinfo=datetime.timezone.utc
            ),
        )

        test_cases = [
            [answer_old, answer_middle, answer_new],
            [answer_old, answer_new, answer_middle],
            [answer_middle, answer_old, answer_new],
            [answer_middle, answer_new, answer_old],
            [answer_new, answer_middle, answer_old],
            [answer_new, answer_old, answer_middle],
        ]
        for answers in test_cases:
            with self.subTest():
                question = OpenKlant2Question(
                    url="http://example.com/question/1",
                    question="What is the final answer?",
                    question_kcm_uuid="q-uuid-1",
                    onderwerp="Philosophy",
                    kanaal="online",
                    taal="nld",
                    nummer="0001",
                    plaatsgevonden_op=datetime.datetime(
                        2024, 10, 2, 14, 0, 0, tzinfo=datetime.timezone.utc
                    ),
                    answers=answers,
                )

                self.assertEqual(question.answer, answer_new)
                self.assertEqual(question.answer.answer, "Final answer")
                self.assertEqual(question.answers[0], answer_new)
                self.assertEqual(question.answers[1], answer_middle)
                self.assertEqual(question.answers[2], answer_old)
                self.assertGreater(
                    question.answer.plaatsgevonden_op,
                    answer_middle.plaatsgevonden_op,
                )
                self.assertGreater(
                    question.answer.plaatsgevonden_op,
                    answer_old.plaatsgevonden_op,
                )

    def test_questions_for_partij_with_no_questions(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        service = OpenKlant2Service(config=self.config)

        with patch.object(service, "klantcontacten_for_partij", return_value=[]):
            questions = service.questions_for_partij("partij-uuid")

        self.assertEqual(questions, [])

    def test_questions_for_partij_question_without_answers(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        service = OpenKlant2Service(config=self.config)

        question_kc = {
            "uuid": "q-uuid-1",
            "inhoud": "What was the question?",
            "onderwerp": "Philosophy",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0001",
            "plaatsgevondenOp": "2024-10-02T14:00:00Z",
            "url": "http://example.com/question/1",
            "gingOverOnderwerpobjecten": [],
        }

        with patch.object(
            service, "klantcontacten_for_partij", return_value=[question_kc]
        ):
            questions = service.questions_for_partij("partij-uuid")

        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0].question_kcm_uuid, "q-uuid-1")
        self.assertEqual(questions[0].question, "What was the question?")
        self.assertEqual(questions[0].answers, [])
        self.assertIsNone(questions[0].answer)

    def test_questions_for_partij_with_question_and_one_answer(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        service = OpenKlant2Service(config=self.config)

        # Question klantcontact
        question_kc = {
            "uuid": "q-uuid-1",
            "inhoud": "What was the question?",
            "onderwerp": "Philosophy",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0001",
            "plaatsgevondenOp": "2024-10-02T14:00:00Z",
            "url": "http://example.com/question/1",
            "gingOverOnderwerpobjecten": [{"uuid": "oo-q-uuid-1"}],
        }

        # Answer klantcontact
        answer_kc = {
            "uuid": "a-uuid-1",
            "inhoud": "42",
            "onderwerp": "Philosophy",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0002",
            "plaatsgevondenOp": "2024-10-02T15:00:00Z",
            "url": "http://example.com/answer/1",
            "gingOverOnderwerpobjecten": [{"uuid": "oo-a-uuid-1"}],
        }

        # Onderwerp_object for question (wasKlantcontact is None/empty)
        question_oo = {
            "uuid": "oo-q-uuid-1",
            "klantcontact": {"uuid": "q-uuid-1"},
            "wasKlantcontact": None,
        }
        # Onderwerp_object for answer (wasKlantcontact points to question)
        answer_oo = {
            "uuid": "oo-a-uuid-1",
            "klantcontact": {"uuid": "a-uuid-1"},
            "wasKlantcontact": {"uuid": "q-uuid-1"},
        }

        # Mock the onderwerp_object.retrieve calls
        mock_client.onderwerp_object.retrieve.side_effect = [
            question_oo,  # First call for question
            answer_oo,  # Second call for answer
        ]

        with patch.object(
            service, "klantcontacten_for_partij", return_value=[question_kc, answer_kc]
        ):
            questions = service.questions_for_partij("partij-uuid")

        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0].question_kcm_uuid, "q-uuid-1")
        self.assertEqual(questions[0].question, "What was the question?")
        self.assertEqual(len(questions[0].answers), 1)
        self.assertEqual(questions[0].answer.answer, "42")
        self.assertEqual(questions[0].answer.answer_kcm_uuid, "a-uuid-1")

        # Verify onderwerp_object.retrieve was called correctly
        self.assertEqual(mock_client.onderwerp_object.retrieve.call_count, 2)
        mock_client.onderwerp_object.retrieve.assert_has_calls(
            [call("oo-q-uuid-1"), call("oo-a-uuid-1")]
        )

    def test_questions_for_partij_with_multiple_answers(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        service = OpenKlant2Service(config=self.config)

        question_kc = {
            "uuid": "q-uuid-1",
            "inhoud": "What was the question?",
            "onderwerp": "Philosophy",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0001",
            "plaatsgevondenOp": "2024-10-02T14:00:00Z",
            "url": "http://example.com/question/1",
            "gingOverOnderwerpobjecten": [{"uuid": "oo-q-uuid-1"}],
        }
        answer_old = {
            "uuid": "a-uuid-1",
            "inhoud": "First answer: 42",
            "onderwerp": "Philosophy",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0002",
            "plaatsgevondenOp": "2024-10-02T15:00:00Z",
            "url": "http://example.com/answer/1",
            "gingOverOnderwerpobjecten": [{"uuid": "oo-a-uuid-1"}],
        }
        answer_middle = {
            "uuid": "a-uuid-2",
            "inhoud": "Updated answer: 43",
            "onderwerp": "Philosophy",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0003",
            "plaatsgevondenOp": "2024-10-02T16:00:00Z",
            "url": "http://example.com/answer/2",
            "gingOverOnderwerpobjecten": [{"uuid": "oo-a-uuid-2"}],
        }
        answer_new = {
            "uuid": "a-uuid-3",
            "inhoud": "Final answer: 44",
            "onderwerp": "Philosophy",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0004",
            "plaatsgevondenOp": "2024-10-02T17:00:00Z",
            "url": "http://example.com/answer/3",
            "gingOverOnderwerpobjecten": [{"uuid": "oo-a-uuid-3"}],
        }

        # Onderwerp_objecten representing answers
        question_oo = {
            "uuid": "oo-q-uuid-1",
            "klantcontact": {"uuid": "q-uuid-1"},
            "wasKlantcontact": None,
        }
        answer_oo_old = {
            "uuid": "oo-a-uuid-1",
            "klantcontact": {"uuid": "a-uuid-1"},
            "wasKlantcontact": {"uuid": "q-uuid-1"},
        }
        answer_oo_middle = {
            "uuid": "oo-a-uuid-2",
            "klantcontact": {"uuid": "a-uuid-2"},
            "wasKlantcontact": {"uuid": "q-uuid-1"},
        }
        answer_oo_new = {
            "uuid": "oo-a-uuid-3",
            "klantcontact": {"uuid": "a-uuid-3"},
            "wasKlantcontact": {"uuid": "q-uuid-1"},
        }

        # Return klantcontacten in random order to test sorting
        mock_client.onderwerp_object.retrieve.side_effect = [
            answer_oo_middle,
            question_oo,
            answer_oo_new,
            answer_oo_old,
        ]

        with patch.object(
            service,
            "klantcontacten_for_partij",
            return_value=[answer_middle, question_kc, answer_new, answer_old],
        ):
            questions = service.questions_for_partij("partij-uuid")

        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0].question_kcm_uuid, "q-uuid-1")
        self.assertEqual(len(questions[0].answers), 3)

        # Verify answers are sorted newest first
        self.assertEqual(questions[0].answers[0].answer_kcm_uuid, "a-uuid-3")
        self.assertEqual(questions[0].answers[0].answer, "Final answer: 44")
        self.assertEqual(questions[0].answers[1].answer_kcm_uuid, "a-uuid-2")
        self.assertEqual(questions[0].answers[1].answer, "Updated answer: 43")
        self.assertEqual(questions[0].answers[2].answer_kcm_uuid, "a-uuid-1")
        self.assertEqual(questions[0].answers[2].answer, "First answer: 42")

        # Verify .answer property returns the newest
        self.assertEqual(questions[0].answer.answer_kcm_uuid, "a-uuid-3")
        self.assertEqual(questions[0].answer.answer, "Final answer: 44")

    def test_questions_for_partij_with_multiple_questions(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        service = OpenKlant2Service(config=self.config)

        # Question 1: no answers
        q1_kc = {
            "uuid": "q-uuid-1",
            "inhoud": "Question 1?",
            "onderwerp": "Topic 1",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0001",
            "plaatsgevondenOp": "2024-10-01T10:00:00Z",
            "url": "http://example.com/q1",
            "gingOverOnderwerpobjecten": [],
        }

        # Question 2: one answer
        q2_kc = {
            "uuid": "q-uuid-2",
            "inhoud": "Question 2?",
            "onderwerp": "Topic 2",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0002",
            "plaatsgevondenOp": "2024-10-02T10:00:00Z",
            "url": "http://example.com/q2",
            "gingOverOnderwerpobjecten": [{"uuid": "oo-q2"}],
        }
        a2_kc = {
            "uuid": "a-uuid-2",
            "inhoud": "Answer to Q2",
            "onderwerp": "Topic 2",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0003",
            "plaatsgevondenOp": "2024-10-02T11:00:00Z",
            "url": "http://example.com/a2",
            "gingOverOnderwerpobjecten": [{"uuid": "oo-a2"}],
        }

        # Question 3: two answers
        q3_kc = {
            "uuid": "q-uuid-3",
            "inhoud": "Question 3?",
            "onderwerp": "Topic 3",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0004",
            "plaatsgevondenOp": "2024-10-03T10:00:00Z",
            "url": "http://example.com/q3",
            "gingOverOnderwerpobjecten": [{"uuid": "oo-q3"}],
        }
        a3_1_kc = {
            "uuid": "a-uuid-3-1",
            "inhoud": "First answer to Q3",
            "onderwerp": "Topic 3",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0005",
            "plaatsgevondenOp": "2024-10-03T11:00:00Z",
            "url": "http://example.com/a3-1",
            "gingOverOnderwerpobjecten": [{"uuid": "oo-a3-1"}],
        }
        a3_2_kc = {
            "uuid": "a-uuid-3-2",
            "inhoud": "Second answer to Q3",
            "onderwerp": "Topic 3",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0006",
            "plaatsgevondenOp": "2024-10-03T12:00:00Z",
            "url": "http://example.com/a3-2",
            "gingOverOnderwerpobjecten": [{"uuid": "oo-a3-2"}],
        }

        # Onderwerp_objecten representing answers
        q2_oo = {"uuid": "oo-q2", "wasKlantcontact": None}
        a2_oo = {"uuid": "oo-a2", "wasKlantcontact": {"uuid": "q-uuid-2"}}
        q3_oo = {"uuid": "oo-q3", "wasKlantcontact": None}
        a3_1_oo = {"uuid": "oo-a3-1", "wasKlantcontact": {"uuid": "q-uuid-3"}}
        a3_2_oo = {"uuid": "oo-a3-2", "wasKlantcontact": {"uuid": "q-uuid-3"}}

        mock_client.onderwerp_object.retrieve.side_effect = [
            q2_oo,
            a2_oo,
            q3_oo,
            a3_1_oo,
            a3_2_oo,
        ]

        with patch.object(
            service,
            "klantcontacten_for_partij",
            return_value=[q1_kc, q2_kc, a2_kc, q3_kc, a3_1_kc, a3_2_kc],
        ):
            questions = service.questions_for_partij("partij-uuid")

        self.assertEqual(len(questions), 3)

        q1 = next(q for q in questions if q.question_kcm_uuid == "q-uuid-1")
        q2 = next(q for q in questions if q.question_kcm_uuid == "q-uuid-2")
        q3 = next(q for q in questions if q.question_kcm_uuid == "q-uuid-3")

        # Q1: no answers
        self.assertEqual(q1.question, "Question 1?")
        self.assertEqual(len(q1.answers), 0)
        self.assertIsNone(q1.answer)

        # Q2: one answer
        self.assertEqual(q2.question, "Question 2?")
        self.assertEqual(len(q2.answers), 1)
        self.assertEqual(q2.answer.answer, "Answer to Q2")

        # Q3: two answers (sorted newest first)
        self.assertEqual(q3.question, "Question 3?")
        self.assertEqual(len(q3.answers), 2)
        self.assertEqual(q3.answers[0].answer, "Second answer to Q3")
        self.assertEqual(q3.answers[1].answer, "First answer to Q3")
        self.assertEqual(q3.answer.answer, "Second answer to Q3")

    def test_questions_for_partij_missing_inhoud(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        service = OpenKlant2Service(config=self.config)

        # Question 1: question misses inhoud
        q1_kc = {
            "uuid": "q-uuid-1",
            "inhoud": None,
            "onderwerp": "Topic 1",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0001",
            "plaatsgevondenOp": "2024-10-01T10:00:00Z",
            "url": "http://example.com/q1",
            "gingOverOnderwerpobjecten": [],
        }

        # Question 2: one answer with missing inhoud
        q2_kc = {
            "uuid": "q-uuid-2",
            "inhoud": "Question 2?",
            "onderwerp": "Topic 2",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0002",
            "plaatsgevondenOp": "2024-10-02T10:00:00Z",
            "url": "http://example.com/q2",
            "gingOverOnderwerpobjecten": [{"uuid": "oo-q2"}],
        }
        a2_kc = {
            "uuid": "a-uuid-2",
            "inhoud": None,
            "onderwerp": "Topic 2",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0003",
            "plaatsgevondenOp": "2024-10-02T11:00:00Z",
            "url": "http://example.com/a2",
            "gingOverOnderwerpobjecten": [{"uuid": "oo-a2"}],
        }

        # Question 3: two answers, one with and one without inhoud
        q3_kc = {
            "uuid": "q-uuid-3",
            "inhoud": "Question 3?",
            "onderwerp": "Topic 3",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0004",
            "plaatsgevondenOp": "2024-10-03T10:00:00Z",
            "url": "http://example.com/q3",
            "gingOverOnderwerpobjecten": [{"uuid": "oo-q3"}],
        }
        a3_1_kc = {
            "uuid": "a-uuid-3-1",
            "inhoud": None,
            "onderwerp": "Topic 3",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0005",
            "plaatsgevondenOp": "2024-10-03T11:00:00Z",
            "url": "http://example.com/a3-1",
            "gingOverOnderwerpobjecten": [{"uuid": "oo-a3-1"}],
        }
        a3_2_kc = {
            "uuid": "a-uuid-3-2",
            "inhoud": "Second answer to Q3",
            "onderwerp": "Topic 3",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0006",
            "plaatsgevondenOp": "2024-10-03T12:00:00Z",
            "url": "http://example.com/a3-2",
            "gingOverOnderwerpobjecten": [{"uuid": "oo-a3-2"}],
        }

        # Onderwerp_objecten representing answers
        q2_oo = {"uuid": "oo-q2", "wasKlantcontact": None}
        a2_oo = {"uuid": "oo-a2", "wasKlantcontact": {"uuid": "q-uuid-2"}}
        q3_oo = {"uuid": "oo-q3", "wasKlantcontact": None}
        a3_1_oo = {"uuid": "oo-a3-1", "wasKlantcontact": {"uuid": "q-uuid-3"}}
        a3_2_oo = {"uuid": "oo-a3-2", "wasKlantcontact": {"uuid": "q-uuid-3"}}

        mock_client.onderwerp_object.retrieve.side_effect = [
            q2_oo,
            a2_oo,
            q3_oo,
            a3_1_oo,
            a3_2_oo,
        ]

        with patch.object(
            service,
            "klantcontacten_for_partij",
            return_value=[q1_kc, q2_kc, a2_kc, q3_kc, a3_1_kc, a3_2_kc],
        ):
            questions = service.questions_for_partij("partij-uuid")

        self.assertEqual(len(questions), 3)

        # q1 (inhoud=None) is kept as an empty question: dropping it would take any
        # reactions to it along with it
        q1 = next(q for q in questions if q.question_kcm_uuid == "q-uuid-1")
        self.assertEqual(q1.question, "")

        # q2 is present but its answer (inhoud=None) is skipped
        q2 = next(q for q in questions if q.question_kcm_uuid == "q-uuid-2")
        self.assertEqual(q2.question, "Question 2?")
        self.assertEqual(len(q2.answers), 0)

        # q3 is present; a3_1 (inhoud=None) is skipped, a3_2 survives
        q3 = next(q for q in questions if q.question_kcm_uuid == "q-uuid-3")
        self.assertEqual(q3.question, "Question 3?")
        self.assertEqual(len(q3.answers), 1)
        self.assertEqual(q3.answers[0].answer, "Second answer to Q3")

    def _mock_conversation_client(self, mock_client_class):
        """Build a client for which the listing already returned the conversation.

        Nothing replies to any klantcontact and no uuid names one that can be
        retrieved, so the repair and walk passes find nothing to add. What they do
        with what they find is settled in `test_conversations.py`, against the
        fetcher and a stand-in for it rather than through a mocked client.
        """
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_client.onderwerp_object.list_iter.return_value = []
        mock_client.klant_contact.retrieve.side_effect = make_not_found()

        return mock_client

    def test_a_failed_walk_yields_the_questions_and_reports_incomplete(
        self, mock_client_class
    ):
        question = make_klantcontact("q1", "Question?", "2024-10-01T10:00:00Z")
        mock_client = self._mock_conversation_client(mock_client_class)
        mock_client.onderwerp_object.list_iter.side_effect = OSError("connection reset")

        service = OpenKlant2Service(config=self.config)
        with patch.object(
            service, "klantcontacten_for_partij", return_value=[question]
        ):
            questions, is_incomplete = service._resolve_questions_for_partij("partij")

        self.assertTrue(is_incomplete)
        self.assertEqual([question.question_kcm_uuid for question in questions], ["q1"])

    def test_a_complete_result_is_cached_and_an_incomplete_one_is_not(
        self, mock_client_class
    ):
        question = make_klantcontact("q1", "Question?", "2024-10-01T10:00:00Z")
        mock_client = self._mock_conversation_client(mock_client_class)

        service = OpenKlant2Service(config=self.config)
        with patch.object(
            service, "klantcontacten_for_partij", return_value=[question]
        ) as listing:
            service.questions_for_partij("partij")
            service.questions_for_partij("partij")
            self.assertEqual(listing.call_count, 1)

            # An incomplete result is what the user is asked to retry, so serving it
            # from the cache would make the retry a no-op.
            service.invalidate_questions_cache("partij")
            mock_client.onderwerp_object.list_iter.side_effect = OSError(
                "connection reset"
            )
            service.questions_for_partij("partij")
            service.questions_for_partij("partij")
            self.assertEqual(listing.call_count, 3)

    def test_asking_a_question_forgets_the_cached_listing(self, mock_client_class):
        question = make_klantcontact("q1", "Question?", "2024-10-01T10:00:00Z")
        self._mock_conversation_client(mock_client_class)

        service = OpenKlant2Service(config=self.config)
        with (
            patch.object(service, "_create_klantcontact", return_value=question),
            patch.object(service, "_create_betrokkene_in_klantcontact"),
            patch.object(service, "_create_interne_taak"),
            patch.object(
                service, "klantcontacten_for_partij", return_value=[question]
            ) as listing,
        ):
            service.questions_for_partij("partij")
            service.create_question_for_partij("partij", "Question?", "Philosophy")
            service.questions_for_partij("partij")

        self.assertEqual(listing.call_count, 2)

    def _resolve_one_question(self, mock_client_class, klantcontacten):
        # Resolutions are cached per partij, and these are complete ones, so a caller
        # running several cases against the same partij would keep getting the first.
        self.clear_caches()
        self._mock_conversation_client(mock_client_class)
        service = OpenKlant2Service(config=self.config)

        with patch.object(
            service, "klantcontacten_for_partij", return_value=klantcontacten
        ):
            questions, _ = service._resolve_questions_for_partij("partij")

        self.assertEqual(len(questions), 1)
        return questions[0]

    def test_afgehandeld_requires_every_interne_taak_to_be_done(
        self, mock_client_class
    ):
        cases = [
            ("no taak at all", (), (), False),
            ("the only taak is open", ("te_verwerken",), (), False),
            ("the only taak is done", ("verwerkt",), (), True),
            ("a follow-up taak is still open", ("verwerkt",), ("te_verwerken",), False),
            ("question and reaction both done", ("verwerkt",), ("verwerkt",), True),
            ("only the reaction raised a taak", (), ("verwerkt",), True),
        ]

        for label, question_statuses, reaction_statuses, expected in cases:
            with self.subTest(label):
                question = make_klantcontact(
                    "q1",
                    "Question?",
                    "2024-10-01T10:00:00Z",
                    interne_taak_statuses=question_statuses,
                )
                reaction = make_klantcontact(
                    "r1",
                    "Reaction",
                    "2024-10-02T10:00:00Z",
                    parent_uuid="q1",
                    interne_taak_statuses=reaction_statuses,
                )
                resolved = self._resolve_one_question(
                    mock_client_class, [question, reaction]
                )

                self.assertEqual(resolved.is_afgehandeld, expected)

    def test_a_reaction_without_content_still_counts_towards_afgehandeld(
        self, mock_client_class
    ):
        """Its taak says the question was dealt with, even with nothing to display."""
        question = make_klantcontact("q1", "Question?", "2024-10-01T10:00:00Z")
        reaction = make_klantcontact(
            "r1",
            None,
            "2024-10-02T10:00:00Z",
            parent_uuid="q1",
            interne_taak_statuses=("verwerkt",),
        )

        resolved = self._resolve_one_question(mock_client_class, [question, reaction])

        self.assertEqual(resolved.answers, [])
        self.assertTrue(resolved.is_afgehandeld)

    def test_afgehandeld_outranks_beantwoord_in_the_dto(self, mock_client_class):
        question = make_klantcontact(
            "3f1c9b42-8a4e-4d1b-9a77-1c2e5d6f7a80",
            "Question?",
            "2024-10-01T10:00:00Z",
            interne_taak_statuses=("verwerkt",),
        )
        reaction = make_klantcontact(
            "8c2d1e55-4b6a-4f2c-9d31-7e0a4b5c6d90",
            "Reaction",
            "2024-10-02T10:00:00Z",
            parent_uuid="3f1c9b42-8a4e-4d1b-9a77-1c2e5d6f7a80",
        )
        self._mock_conversation_client(mock_client_class)
        service = OpenKlant2Service(config=self.config)
        user = UserFactory()

        with (
            patch.object(service, "resolve_partij_uuid", return_value="partij"),
            patch.object(
                service, "klantcontacten_for_partij", return_value=[question, reaction]
            ),
        ):
            result = service.list_questions({}, user)

        self.assertEqual(result.questions[0]["status"], str(Status.afgehandeld.label))
        self.assertEqual(result.questions[0]["answer_text"], "Reaction")

    def test_a_question_without_a_taak_keeps_the_answer_based_status(
        self, mock_client_class
    ):
        question = make_klantcontact(
            "3f1c9b42-8a4e-4d1b-9a77-1c2e5d6f7a80", "Question?", "2024-10-01T10:00:00Z"
        )
        self._mock_conversation_client(mock_client_class)
        service = OpenKlant2Service(config=self.config)
        user = UserFactory()

        with (
            patch.object(service, "resolve_partij_uuid", return_value="partij"),
            patch.object(service, "klantcontacten_for_partij", return_value=[question]),
        ):
            result = service.list_questions({}, user)

        self.assertEqual(result.questions[0]["status"], "Onbeantwoord")

    def test_list_questions_reports_an_incomplete_resolution(self, mock_client_class):
        """The flag has to reach QuestionsResult, which is what raises the banner."""
        # A real uuid: unlike the graph tests, this one reaches the DTO builder,
        # which validates it.
        question = make_klantcontact(
            "3f1c9b42-8a4e-4d1b-9a77-1c2e5d6f7a80",
            "Question?",
            "2024-10-01T10:00:00Z",
        )
        mock_client = self._mock_conversation_client(mock_client_class)
        mock_client.onderwerp_object.list_iter.side_effect = OSError("connection reset")

        service = OpenKlant2Service(config=self.config)
        user = UserFactory()

        with (
            patch.object(service, "resolve_partij_uuid", return_value="partij"),
            patch.object(service, "klantcontacten_for_partij", return_value=[question]),
        ):
            result = service.list_questions({}, user)

        self.assertTrue(result.is_incomplete)
        self.assertEqual(len(result.questions), 1)

    def test_retrieve_question_returns_none_when_uuid_not_found(
        self, mock_client_class
    ):
        """A question_uuid absent from the partij's questions must 404, not crash.

        `next()` without a default previously raised `StopIteration` here, which the
        view's exception handling does not catch.
        """
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        service = OpenKlant2Service(config=self.config)
        user = UserFactory()

        question_kc = {
            "uuid": "q-uuid-1",
            "inhoud": "What was the question?",
            "onderwerp": "Philosophy",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0001",
            "plaatsgevondenOp": "2024-10-02T14:00:00Z",
            "url": "http://example.com/question/1",
            "gingOverOnderwerpobjecten": [],
        }

        with (
            patch.object(
                service, "find_persoon_for_bsn", return_value={"uuid": "partij-uuid"}
            ),
            patch.object(
                service, "klantcontacten_for_partij", return_value=[question_kc]
            ),
        ):
            result = service.retrieve_question(
                fetch_params={"user_bsn": "123456789"},
                question_uuid="nonexistent-uuid",
                user=user,
            )

        self.assertEqual(result, (None, None))


class NormalizeHelpersTestCase(TestCase):
    def test_normalize(self):
        cases = [
            (_normalize_phone, "06-12 345 678", "0612345678"),
            (_normalize_phone, "+31 6 12 34 56 78", "0031612345678"),
            (_normalize_phone, "  0612345678  ", "0612345678"),
            (_normalize_email, "User@Example.COM", "user@example.com"),
            (_normalize_email, "  user@example.com  ", "user@example.com"),
        ]
        for fn, value, expected in cases:
            with self.subTest(fn=fn.__name__, value=value):
                self.assertEqual(fn(value), expected, f"{fn.__name__}({value!r})")


def _make_digitaal_adres(adres, soort, is_standaard=True, uuid_str="addr-uuid"):
    return {
        "uuid": uuid_str,
        "soortDigitaalAdres": soort,
        "adres": adres,
        "isStandaardAdres": is_standaard,
        "omschrijving": "OIP profiel",
        "verstrektDoorPartij": {"uuid": "partij-uuid"},
        "verstrektDoorBetrokkene": None,
    }


@patch("open_inwoner.openklant.services.OpenKlantClient")
class GetOrCreateDigitaalAdresNormalizationTestCase(TestCase):
    """Deduplication must survive formatting differences in stored vs incoming values."""

    def setUp(self):
        self.config = OpenKlant2ConfigFactory()

    def _service_with_existing(self, mock_client_class, existing_adres):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.digitaal_adres.list.return_value = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [existing_adres],
        }
        return OpenKlant2Service(config=self.config), mock_client

    def test_phone_not_duplicated_when_formatting_differs(self, mock_client_class):
        existing = _make_digitaal_adres("06-12 345 678", "telefoonnummer")
        service, mock_client = self._service_with_existing(mock_client_class, existing)

        _, created = service.get_or_create_digitaal_adres_for_partij(
            partij_uuid="partij-uuid",
            soort_adres="telefoonnummer",
            adres="0612345678",
            is_standaard_adres=True,
        )

        self.assertFalse(created)
        mock_client.digitaal_adres.create.assert_not_called()

    def test_phone_not_duplicated_when_international_format_differs(
        self, mock_client_class
    ):
        existing = _make_digitaal_adres("+31 6 12345678", "telefoonnummer")
        service, mock_client = self._service_with_existing(mock_client_class, existing)

        _, created = service.get_or_create_digitaal_adres_for_partij(
            partij_uuid="partij-uuid",
            soort_adres="telefoonnummer",
            adres="+31612345678",
            is_standaard_adres=True,
        )

        self.assertFalse(created)
        mock_client.digitaal_adres.create.assert_not_called()

    def test_email_not_duplicated_when_case_differs(self, mock_client_class):
        existing = _make_digitaal_adres("User@Example.COM", "email", is_standaard=False)
        service, mock_client = self._service_with_existing(mock_client_class, existing)

        _, created = service.get_or_create_digitaal_adres_for_partij(
            partij_uuid="partij-uuid",
            soort_adres="email",
            adres="user@example.com",
            is_standaard_adres=False,
        )

        self.assertFalse(created)
        mock_client.digitaal_adres.create.assert_not_called()

    def test_phone_created_normalized_when_no_existing(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.digitaal_adres.list.return_value = {
            "count": 0,
            "next": None,
            "previous": None,
            "results": [],
        }
        mock_client.digitaal_adres.create.return_value = _make_digitaal_adres(
            "0612345678", "telefoonnummer"
        )

        service = OpenKlant2Service(config=self.config)
        service.get_or_create_digitaal_adres_for_partij(
            partij_uuid="partij-uuid",
            soort_adres="telefoonnummer",
            adres="06-12 345 678",
            is_standaard_adres=True,
        )

        create_call = mock_client.digitaal_adres.create.call_args
        self.assertEqual(create_call[1]["data"]["adres"], "0612345678")

    def test_email_created_normalized_when_no_existing(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.digitaal_adres.list.return_value = {
            "count": 0,
            "next": None,
            "previous": None,
            "results": [],
        }
        mock_client.digitaal_adres.create.return_value = _make_digitaal_adres(
            "user@example.com", "email", is_standaard=False
        )

        service = OpenKlant2Service(config=self.config)
        service.get_or_create_digitaal_adres_for_partij(
            partij_uuid="partij-uuid",
            soort_adres="email",
            adres="  User@Example.COM  ",
            is_standaard_adres=False,
        )

        create_call = mock_client.digitaal_adres.create.call_args
        self.assertEqual(create_call[1]["data"]["adres"], "user@example.com")

    def test_different_phone_still_creates_new(self, mock_client_class):
        existing = _make_digitaal_adres("0612345678", "telefoonnummer")
        service, mock_client = self._service_with_existing(mock_client_class, existing)
        mock_client.digitaal_adres.create.return_value = _make_digitaal_adres(
            "0687654321", "telefoonnummer", uuid_str="new-uuid"
        )

        _, created = service.get_or_create_digitaal_adres_for_partij(
            partij_uuid="partij-uuid",
            soort_adres="telefoonnummer",
            adres="0687654321",
            is_standaard_adres=True,
        )

        self.assertTrue(created)
        mock_client.digitaal_adres.create.assert_called_once()

    def test_not_duplicated_when_only_is_standaard_differs(self, mock_client_class):
        existing = _make_digitaal_adres(
            "0612345678", "telefoonnummer", is_standaard=True
        )
        service, mock_client = self._service_with_existing(mock_client_class, existing)

        _, created = service.get_or_create_digitaal_adres_for_partij(
            partij_uuid="partij-uuid",
            soort_adres="telefoonnummer",
            adres="0612345678",
            is_standaard_adres=False,
        )

        self.assertFalse(created)
        mock_client.digitaal_adres.create.assert_not_called()
        mock_client.digitaal_adres.partial_update.assert_not_called()

    def test_not_duplicated_when_is_standaard_adres_is_none(self, mock_client_class):
        existing = _make_digitaal_adres(
            "0612345678", "telefoonnummer", is_standaard=True
        )
        service, mock_client = self._service_with_existing(mock_client_class, existing)

        _, created = service.get_or_create_digitaal_adres_for_partij(
            partij_uuid="partij-uuid",
            soort_adres="telefoonnummer",
            adres="0612345678",
        )

        self.assertFalse(created)
        mock_client.digitaal_adres.create.assert_not_called()
        mock_client.digitaal_adres.partial_update.assert_not_called()

    def test_patches_is_standaard_when_existing_is_not_standaard(
        self, mock_client_class
    ):
        existing = _make_digitaal_adres(
            "0612345678", "telefoonnummer", is_standaard=False
        )
        service, mock_client = self._service_with_existing(mock_client_class, existing)
        patched = _make_digitaal_adres(
            "0612345678", "telefoonnummer", is_standaard=True
        )
        mock_client.digitaal_adres.partial_update.return_value = patched

        result, created = service.get_or_create_digitaal_adres_for_partij(
            partij_uuid="partij-uuid",
            soort_adres="telefoonnummer",
            adres="0612345678",
            is_standaard_adres=True,
        )

        self.assertFalse(created)
        mock_client.digitaal_adres.create.assert_not_called()
        mock_client.digitaal_adres.partial_update.assert_called_once_with(
            "addr-uuid", data={"isStandaardAdres": True}
        )
        self.assertEqual(result, patched)


@patch("open_inwoner.openklant.services.OpenKlantClient")
class UpdatePartijFromUserDataTestCase(TestCase):
    PARTIJ_UUID = "partij-uuid-1234"

    def setUp(self):
        self.config = OpenKlant2ConfigFactory()

    def _make_adres(self, uuid, soort, adres, is_standaard=False):
        return {
            "uuid": uuid,
            "soortDigitaalAdres": soort,
            "adres": adres,
            "isStandaardAdres": is_standaard,
            "omschrijving": "OIP profiel",
            "verstrektDoorPartij": {"uuid": self.PARTIJ_UUID},
            "verstrektDoorBetrokkene": None,
        }

    def _list_response(self, results):
        return {
            "count": len(results),
            "next": None,
            "previous": None,
            "results": results,
        }

    def test_fetches_adressen_exactly_once_for_multiple_addresses(
        self, mock_client_class
    ):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.digitaal_adres.list.return_value = self._list_response([])
        mock_client.digitaal_adres.create.side_effect = [
            self._make_adres(
                "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee", "email", "test@example.com"
            ),
            self._make_adres(
                "ffffffff-ffff-ffff-ffff-ffffffffffff",
                "telefoonnummer",
                "0612345678",
                is_standaard=True,
            ),
        ]

        user = DigidUserFactory()
        DigitalAddressFactory(
            user=user, type=DigitalAddressType.email, value="test@example.com"
        )
        DigitalAddressFactory(
            user=user,
            type=DigitalAddressType.phone,
            value="0612345678",
            is_standard_for_type=True,
        )

        service = OpenKlant2Service(config=self.config)
        service.update_partij_from_user_data(partij_uuid=self.PARTIJ_UUID, user=user)

        mock_client.digitaal_adres.list.assert_called_once()

    def test_returns_empty_when_user_has_no_digital_addresses(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        user = DigidUserFactory()

        service = OpenKlant2Service(config=self.config)
        result = service.update_partij_from_user_data(
            partij_uuid=self.PARTIJ_UUID, user=user
        )

        self.assertEqual(result, [])
        mock_client.digitaal_adres.create.assert_not_called()
        mock_client.digitaal_adres.list.assert_not_called()

    def test_mapping_patches_remote_address_via_uuid(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        user = DigidUserFactory()
        address = DigitalAddressFactory(
            user=user,
            type=DigitalAddressType.email,
            value="test@example.com",
            is_standard_for_type=True,
        )
        DigitaalAdresOpenKlantMappingFactory(
            digital_address=address, ok_uuid="cccccccc-cccc-cccc-cccc-cccccccccccc"
        )

        service = OpenKlant2Service(config=self.config)
        result = service.update_partij_from_user_data(
            partij_uuid=self.PARTIJ_UUID, user=user
        )

        mock_client.digitaal_adres.partial_update.assert_called_once_with(
            "cccccccc-cccc-cccc-cccc-cccccccccccc",
            data={"adres": "test@example.com", "isStandaardAdres": True},
        )
        mock_client.digitaal_adres.list.assert_not_called()
        mock_client.digitaal_adres.create.assert_not_called()
        self.assertEqual(result, [])

    def test_creates_missing_adres_and_reports_field(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.digitaal_adres.list.return_value = self._list_response([])
        mock_client.digitaal_adres.create.return_value = self._make_adres(
            "11111111-1111-1111-1111-111111111111", "email", "new@example.com"
        )

        user = DigidUserFactory()
        DigitalAddressFactory(
            user=user, type=DigitalAddressType.email, value="new@example.com"
        )

        service = OpenKlant2Service(config=self.config)
        result = service.update_partij_from_user_data(
            partij_uuid=self.PARTIJ_UUID, user=user
        )

        self.assertEqual(result, ["digitaleAddresen.email"])
        mock_client.digitaal_adres.create.assert_called_once()

    def test_phone_standard_created_as_standaard_adres(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.digitaal_adres.list.return_value = self._list_response([])
        mock_client.digitaal_adres.create.return_value = self._make_adres(
            "22222222-2222-2222-2222-222222222222",
            "telefoonnummer",
            "0612345678",
            is_standaard=True,
        )

        user = DigidUserFactory()
        DigitalAddressFactory(
            user=user,
            type=DigitalAddressType.phone,
            value="0612345678",
            is_standard_for_type=True,
        )

        service = OpenKlant2Service(config=self.config)
        service.update_partij_from_user_data(partij_uuid=self.PARTIJ_UUID, user=user)

        create_data = mock_client.digitaal_adres.create.call_args[1]["data"]
        self.assertTrue(create_data["isStandaardAdres"])
        self.assertEqual(create_data["soortDigitaalAdres"], "telefoonnummer")

    def test_phone_non_standard_created_as_non_standaard_adres(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.digitaal_adres.list.return_value = self._list_response([])
        mock_client.digitaal_adres.create.return_value = self._make_adres(
            "33333333-3333-3333-3333-333333333333",
            "telefoonnummer",
            "0687654321",
            is_standaard=False,
        )

        user = DigidUserFactory()
        DigitalAddressFactory(
            user=user,
            type=DigitalAddressType.phone,
            value="0687654321",
            is_standard_for_type=False,
        )

        service = OpenKlant2Service(config=self.config)
        service.update_partij_from_user_data(partij_uuid=self.PARTIJ_UUID, user=user)

        create_data = mock_client.digitaal_adres.create.call_args[1]["data"]
        self.assertFalse(create_data["isStandaardAdres"])
        self.assertEqual(create_data["soortDigitaalAdres"], "telefoonnummer")

    def test_newly_created_adres_visible_to_subsequent_addresses_without_extra_fetch(
        self, mock_client_class
    ):
        """
        A newly created address is appended locally so the next address can value-match
        against the same list — no second API call.
        """
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.digitaal_adres.list.return_value = self._list_response([])
        mock_client.digitaal_adres.create.side_effect = [
            self._make_adres(
                "44444444-4444-4444-4444-444444444444",
                "telefoonnummer",
                "0612345678",
                is_standaard=True,
            ),
            self._make_adres(
                "55555555-5555-5555-5555-555555555555",
                "telefoonnummer",
                "0687654321",
                is_standaard=False,
            ),
        ]

        user = DigidUserFactory()
        DigitalAddressFactory(
            user=user,
            type=DigitalAddressType.phone,
            value="0612345678",
            is_standard_for_type=True,
        )
        DigitalAddressFactory(
            user=user,
            type=DigitalAddressType.phone,
            value="0687654321",
            is_standard_for_type=False,
        )

        service = OpenKlant2Service(config=self.config)
        result = service.update_partij_from_user_data(
            partij_uuid=self.PARTIJ_UUID, user=user
        )

        self.assertEqual(mock_client.digitaal_adres.list.call_count, 1)
        self.assertEqual(mock_client.digitaal_adres.create.call_count, 2)
        self.assertEqual(result.count("digitaleAddresen.telefoonnummer"), 2)

    def test_backfill_reuses_existing_remote_address(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        existing_standard = self._make_adres(
            "66666666-6666-6666-6666-666666666666",
            "telefoonnummer",
            "0612345678",
            is_standaard=True,
        )
        mock_client.digitaal_adres.list.return_value = self._list_response(
            [existing_standard]
        )
        mock_client.digitaal_adres.create.return_value = self._make_adres(
            "77777777-7777-7777-7777-777777777777",
            "telefoonnummer",
            "0687654321",
            is_standaard=False,
        )

        user = DigidUserFactory()
        DigitalAddressFactory(
            user=user,
            type=DigitalAddressType.phone,
            value="0612345678",
            is_standard_for_type=True,
        )
        DigitalAddressFactory(
            user=user,
            type=DigitalAddressType.phone,
            value="0687654321",
            is_standard_for_type=False,
        )

        service = OpenKlant2Service(config=self.config)
        result = service.update_partij_from_user_data(
            partij_uuid=self.PARTIJ_UUID, user=user
        )

        mock_client.digitaal_adres.list.assert_called_once()
        mock_client.digitaal_adres.create.assert_called_once()
        self.assertEqual(result, ["digitaleAddresen.telefoonnummer"])


@patch("open_inwoner.openklant.services.OpenKlantClient")
class ListQuestionsForZaakTestCase(TestCase):
    PARTIJ_UUID = "partij-uuid-1234"
    ZAAK_UUID = "6d3f2b1a-0c4e-4f8a-9b7c-1e2d3f4a5b6c"

    def setUp(self):
        self.config = OpenKlant2ConfigFactory()
        self.user = UserFactory()
        self.zaak = Mock(url=f"http://zaken.nl/api/v1/zaken/{self.ZAAK_UUID}")

    def _make_kc(self, uuid, *, initiator=True, parent_uuid=None):
        """A klantcontact on the zaak, optionally replying to another one."""
        klantcontact = make_klantcontact(
            uuid, "Question?", "2024-10-01T10:00:00Z", parent_uuid=parent_uuid
        )
        klantcontact["_expand"]["hadBetrokkenen"] = [
            {"initiator": initiator, "wasPartij": {"uuid": self.PARTIJ_UUID}}
        ]
        return klantcontact

    def _list_questions(self, mock_client_class, klantcontacten):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.klant_contact.list_iter.return_value = iter(klantcontacten)

        service = OpenKlant2Service(config=self.config)
        with patch.object(
            service, "get_partij_for_user", return_value={"uuid": self.PARTIJ_UUID}
        ):
            questions = service.list_questions_for_zaak(self.zaak, self.user)

        return mock_client, [str(question["api_source_uuid"]) for question in questions]

    def test_question_by_citizen_is_listed(self, mock_client_class):
        question_uuid = "11111111-1111-1111-1111-111111111111"

        _, listed = self._list_questions(
            mock_client_class, [self._make_kc(question_uuid)]
        )

        self.assertEqual(listed, [question_uuid])

    def test_reaction_on_zaak_is_not_listed_as_question(self, mock_client_class):
        """A reaction can carry the zaak identificator alongside its `wasKlantcontact`.

        Registered with the citizen as initiator it passes that check, so without the
        reply check it would be shown as something the citizen asked.
        """
        question_uuid = "11111111-1111-1111-1111-111111111111"
        reaction_uuid = "22222222-2222-2222-2222-222222222222"

        _, listed = self._list_questions(
            mock_client_class,
            [
                self._make_kc(question_uuid),
                self._make_kc(reaction_uuid, parent_uuid=question_uuid),
            ],
        )

        self.assertEqual(listed, [question_uuid])

    def test_klantcontact_not_initiated_by_citizen_is_not_listed(
        self, mock_client_class
    ):
        _, listed = self._list_questions(
            mock_client_class,
            [self._make_kc("11111111-1111-1111-1111-111111111111", initiator=False)],
        )

        self.assertEqual(listed, [])

    def test_listing_expands_needed_onderwerpobjecten(self, mock_client_class):
        """Without the expand every row would read as a question."""
        mock_client, _ = self._list_questions(mock_client_class, [])

        params = mock_client.klant_contact.list_iter.call_args.kwargs["params"]
        self.assertIn("gingOverOnderwerpobjecten", params["expand"])
        self.assertEqual(
            params["onderwerpobject__onderwerpobjectidentificatorObjectId"],
            self.ZAAK_UUID,
        )


@patch("open_inwoner.openklant.services.OpenKlantClient")
class KlantcontactenForPartijTestCase(TestCase):
    PARTIJ_UUID = "partij-uuid-1234"

    def setUp(self):
        self.config = OpenKlant2ConfigFactory()

    def _make_kc(self, uuid, partij_uuid=None, initiator=True, expand_key="_expand"):
        betrokkene = {"initiator": initiator}
        if partij_uuid is not None:
            betrokkene["wasPartij"] = {"uuid": partij_uuid}
        else:
            betrokkene["wasPartij"] = None
        return {
            "uuid": uuid,
            expand_key: {"hadBetrokkenen": [betrokkene]},
        }

    def test_matching_klantcontact_is_returned(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        kc = self._make_kc("kc-1", partij_uuid=self.PARTIJ_UUID, initiator=True)
        mock_client.klant_contact.list_iter.return_value = iter([kc])

        service = OpenKlant2Service(config=self.config)
        result = list(service.klantcontacten_for_partij(self.PARTIJ_UUID))

        self.assertEqual(result, [kc])

    def test_different_partij_uuid_is_excluded(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        kc = self._make_kc("kc-1", partij_uuid="other-partij-uuid", initiator=True)
        mock_client.klant_contact.list_iter.return_value = iter([kc])

        service = OpenKlant2Service(config=self.config)
        result = list(service.klantcontacten_for_partij(self.PARTIJ_UUID))

        self.assertEqual(result, [])

    def test_non_initiator_is_included(self, mock_client_class):
        """A reaction registered by an employee has the partij as a non-initiator."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        kc = self._make_kc("kc-1", partij_uuid=self.PARTIJ_UUID, initiator=False)
        mock_client.klant_contact.list_iter.return_value = iter([kc])

        service = OpenKlant2Service(config=self.config)
        result = list(service.klantcontacten_for_partij(self.PARTIJ_UUID))

        self.assertEqual(result, [kc])

    def test_listing_is_not_filtered_on_kanaal(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.klant_contact.list_iter.return_value = iter([])

        service = OpenKlant2Service(config=self.config)
        list(service.klantcontacten_for_partij(self.PARTIJ_UUID))

        params = mock_client.klant_contact.list_iter.call_args[1]["params"]
        self.assertNotIn("kanaal", params)
        self.assertEqual(params["hadBetrokkene__wasPartij__uuid"], self.PARTIJ_UUID)
        self.assertEqual(params["pageSize"], 500)

    def test_missing_expand_key_is_excluded_without_exception(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        kc = {"uuid": "kc-bad"}  # no _expand key at all
        mock_client.klant_contact.list_iter.return_value = iter([kc])

        service = OpenKlant2Service(config=self.config)
        result = list(service.klantcontacten_for_partij(self.PARTIJ_UUID))

        self.assertEqual(result, [])

    def test_missing_had_betrokkenen_in_expand_is_excluded_without_exception(
        self, mock_client_class
    ):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        kc = {"uuid": "kc-bad", "_expand": {}}  # hadBetrokkenen absent
        mock_client.klant_contact.list_iter.return_value = iter([kc])

        service = OpenKlant2Service(config=self.config)
        result = list(service.klantcontacten_for_partij(self.PARTIJ_UUID))

        self.assertEqual(result, [])

    def test_null_was_partij_is_excluded_without_exception(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        # wasPartij is null — the betrokkene belongs to no partij
        kc = self._make_kc("kc-1", partij_uuid=None, initiator=True)
        mock_client.klant_contact.list_iter.return_value = iter([kc])

        service = OpenKlant2Service(config=self.config)
        result = list(service.klantcontacten_for_partij(self.PARTIJ_UUID))

        self.assertEqual(result, [])

    def test_malformed_items_excluded_valid_items_returned(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        good = self._make_kc("kc-good", partij_uuid=self.PARTIJ_UUID, initiator=True)
        bad_no_expand = {"uuid": "kc-bad-1"}
        bad_empty_expand = {"uuid": "kc-bad-2", "_expand": {}}
        mock_client.klant_contact.list_iter.return_value = iter(
            [bad_no_expand, bad_empty_expand, good]
        )

        service = OpenKlant2Service(config=self.config)
        result = list(service.klantcontacten_for_partij(self.PARTIJ_UUID))

        self.assertEqual(result, [good])
