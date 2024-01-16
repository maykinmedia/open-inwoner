from unittest import mock

from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.formats import date_format

from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.constants import RolOmschrijving, RolTypes

from open_inwoner.accounts.tests.factories import DigidUserFactory, UserFactory
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.openzaak.notifications import (
    get_initiator_users_from_roles,
    get_np_initiator_bsns_from_roles,
    send_case_update_email,
)
from open_inwoner.openzaak.tests.factories import generate_rol

from ..api_models import Zaak, ZaakType
from .test_notification_data import MockAPIData


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class NotificationHandlerUtilsTestCase(TestCase):
    def test_send_case_update_email(self):
        config = SiteConfiguration.get_solo()
        data = MockAPIData()

        user = data.user_initiator

        case = factory(Zaak, data.zaak)
        case.zaaktype = factory(ZaakType, data.zaak_type)

        case_url = reverse("cases:case_detail", kwargs={"object_id": str(case.uuid)})

        # mock `_format_zaak_identificatie`, but then continue with result of actual call
        # (test redirect for invalid BSN that passes pattern validation)
        ret_val = case._format_zaak_identificatie()
        with mock.patch.object(
            Zaak, "_format_zaak_identificatie"
        ) as format_identificatie:
            format_identificatie.return_value = ret_val
            send_case_update_email(user, case)

        format_identificatie.assert_called_once()

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [user.email])
        self.assertIn(config.name, email.subject)

        body_html = email.alternatives[0][0]
        self.assertIn(case.identificatie, body_html)
        self.assertIn(case.zaaktype.omschrijving, body_html)
        self.assertIn(date_format(case.startdatum), body_html)
        self.assertIn(case_url, body_html)
        self.assertIn(config.name, body_html)

    # TODO we're missing a similar test for get_nnp_initiator_nnp_id_from_roles()
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
        roles = [
            find_rol_1,
            find_rol_2,
            # add some roles we're not interested in
            #
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
        # filtered and de-duplicated
        expected = {
            "100000001",
            "100000002",
        }
        actual = get_np_initiator_bsns_from_roles(roles)
        self.assertEqual(set(actual), expected)

    def test_get_initiator_users_from_roles(self):
        # users we're interested in
        user_1 = DigidUserFactory(
            bsn="100000001", first_name="user_1", email="user_1@example.com"
        )
        user_2 = DigidUserFactory(
            bsn="100000002", first_name="user_2", email="user_2@example.com"
        )

        # not active
        user_not_active = DigidUserFactory(
            bsn="404000003",
            is_active=False,
            first_name="not_active",
            email="user_not_active@example.com",
        )

        # bad role
        user_bad_role = DigidUserFactory(
            bsn="404000006", first_name="bad_role", email="user_bad_role@example.com"
        )

        # not part of roles
        user_not_a_role = DigidUserFactory(
            bsn="404000007",
            first_name="not_a_role",
            email="user_not_a_role@example.com",
        )

        # not a digid user
        user_no_bsn = UserFactory(
            bsn="", first_name="no_bsn", email="user_no_bsn@example.com"
        )

        # good roles
        role_1 = generate_rol(
            RolTypes.natuurlijk_persoon,
            {"inpBsn": user_1.bsn},
            RolOmschrijving.initiator,
        )
        role_2 = generate_rol(
            RolTypes.natuurlijk_persoon,
            {"inpBsn": user_2.bsn},
            RolOmschrijving.medeinitiator,
        )
        roles = [
            role_1,
            role_2,
            # add some bad roles
            generate_rol(
                RolTypes.natuurlijk_persoon,
                {"inpBsn": user_not_active.bsn},
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

        # verify we have a lot of Roles with initiators & bsn's
        check_roles = get_np_initiator_bsns_from_roles(roles)
        expected_roles = {
            user_1.bsn,
            user_2.bsn,
            user_not_active.bsn,
        }
        self.assertEqual(set(check_roles), expected_roles)

        # of all the Users with Roles only these match all conditions
        expected = {user_1, user_2}
        actual = get_initiator_users_from_roles(roles)

        self.assertEqual(set(actual), expected)
