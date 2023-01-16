from unittest import expectedFailure
from unittest.mock import patch

from django.test import TestCase

from zgw_consumers.api_models.constants import RolOmschrijving, RolTypes

from open_inwoner.accounts.tests.factories import DigidUserFactory, UserFactory
from open_inwoner.openzaak.notifications import (
    get_emailable_initiator_users_from_roles,
    get_np_initiator_bsns_from_roles,
    handle_zaken_notification,
)
from open_inwoner.openzaak.tests.factories import NotificationFactory, generate_rol


class NotificationHandlerTestCase(TestCase):
    @expectedFailure
    @patch("open_inwoner.openzaak.notifications.handle_status_update")
    def test_main_handler_routes_zaak_resource(self, mock_handle):
        notification = NotificationFactory(resource="zaak")

        handle_zaken_notification(notification)

        mock_handle.assert_called_once_with(notification)


class NotificationHandlerUtilsTestCase(TestCase):
    def test_get_np_initiator_bsns_from_roles(self):
        # roles we're interested in
        find_rol_1 = generate_rol(
            RolTypes.natuurlijk_persoon,
            {"inpBsn": "100000001"},
            RolOmschrijving.initiator,
        )
        find_rol_2 = generate_rol(
            RolTypes.natuurlijk_persoon,
            {"inpBsn": "100000002"},
            RolOmschrijving.medeinitiator,
        )
        roles = [find_rol_1, find_rol_2]

        # add roles we're not interested in
        roles.extend(
            [
                # interested but duplicate BSN
                generate_rol(
                    RolTypes.natuurlijk_persoon,
                    {"inpBsn": "100000001"},
                    RolOmschrijving.medeinitiator,
                ),
                # bad type
                generate_rol(
                    RolTypes.vestiging,
                    {"inpBsn": "404000001"},
                    RolOmschrijving.initiator,
                ),
                # bad description
                generate_rol(
                    RolTypes.natuurlijk_persoon,
                    {"inpBsn": "404000002"},
                    RolOmschrijving.behandelaar,
                ),
                # bad identification
                generate_rol(
                    RolTypes.natuurlijk_persoon,
                    {"not_the_expected_field": 123},
                    RolOmschrijving.initiator,
                ),
            ]
        )
        # filtered and de-duplicated
        expected = {
            "100000001",
            "100000002",
        }
        actual = get_np_initiator_bsns_from_roles(roles)
        self.assertEqual(set(actual), expected)

    def test_get_emailable_initiator_users_from_roles(self):
        # users we want to find
        user_1 = DigidUserFactory(bsn="100000001", email="user_1@example.com")
        user_2 = DigidUserFactory(bsn="100000002", email="user_2@example.com")

        # not active
        user_not_active = DigidUserFactory(
            bsn="404000003", is_active=False, email="user_not_active@example.com"
        )

        # no email
        user_no_email = DigidUserFactory(bsn="404000004", email="")

        # placeholder email
        user_placeholder_email = DigidUserFactory(
            bsn="404000005", email="user_placeholder_email@example.org"
        )
        # bad role
        user_bad_role = DigidUserFactory(
            bsn="404000006", email="user_bad_role@example.com"
        )

        # not part of roles
        user_not_a_role = DigidUserFactory(
            bsn="404000007", email="user_not_a_role@example.com"
        )

        # not a digid user
        user_no_bsn = UserFactory(bsn="", email="user_no_bsn@example.com")

        # good roles
        role_1 = generate_rol(
            RolTypes.natuurlijk_persoon,
            {"inpBsn": user_1.bsn},
            RolOmschrijving.initiator,
        )
        role_2 = generate_rol(
            RolTypes.natuurlijk_persoon,
            {"inpBsn": user_2.bsn},
            RolOmschrijving.initiator,
        )
        roles = [role_1, role_2]

        # add some bad roles
        roles.extend(
            [
                generate_rol(
                    RolTypes.natuurlijk_persoon,
                    {"inpBsn": user_not_active.bsn},
                    RolOmschrijving.initiator,
                ),
                generate_rol(
                    RolTypes.natuurlijk_persoon,
                    {"inpBsn": user_no_email.bsn},
                    RolOmschrijving.initiator,
                ),
                generate_rol(
                    RolTypes.natuurlijk_persoon,
                    {"inpBsn": user_placeholder_email.bsn},
                    RolOmschrijving.initiator,
                ),
                generate_rol(
                    RolTypes.natuurlijk_persoon,
                    {"inpBsn": user_bad_role.bsn},
                    RolOmschrijving.behandelaar,
                ),
                # duplicate with different role
                generate_rol(
                    RolTypes.natuurlijk_persoon,
                    {"inpBsn": user_1.bsn},
                    RolOmschrijving.medeinitiator,
                ),
            ]
        )

        # verify we have a lot of Roles with initiators & bsn's
        check_roles = get_np_initiator_bsns_from_roles(roles)
        expected_roles = {
            user_1.bsn,
            user_2.bsn,
            user_not_active.bsn,
            user_no_email.bsn,
            user_placeholder_email.bsn,
        }
        self.assertEqual(set(check_roles), expected_roles)

        # of all the Users with Roles only these match all conditions to actually get notified
        expected = {user_1, user_2}
        actual = get_emailable_initiator_users_from_roles(roles)

        self.assertEqual(set(actual), expected)
