from unittest import mock

from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.constants import RolOmschrijving, RolTypes

from open_inwoner.accounts.tests.factories import DigidUserFactory, UserFactory
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.openzaak.api_models import Status, StatusType, Zaak, ZaakType
from open_inwoner.openzaak.constants import ZaakBetrokkeneRol
from open_inwoner.openzaak.notifications import (
    _get_initiator_users_from_roles,
    _get_nnp_initiator_nnp_id_from_roles,
    _get_np_initiator_bsns_from_roles,
    send_case_update_email,
)
from open_inwoner.openzaak.tests.factories import ZGWApiGroupConfigFactory, generate_rol
from open_inwoner.openzaak.tests.shared import ZAKEN_ROOT

from .test_notification_data import MockAPIData


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class NotificationHandlerUtilsTestCase(TestCase):
    def setUp(self):
        self.api_group = ZGWApiGroupConfigFactory(
            zrc_service__api_root=ZAKEN_ROOT,
            fetch_eherkenning_zaken_with_rsin=False,
        )

    def test_send_case_update_email(self):
        config = SiteConfiguration.get_solo()
        data = MockAPIData()

        user = data.user_initiator

        zaak = factory(Zaak, data.zaak)
        zaak.zaaktype = factory(ZaakType, data.zaak_type)

        status = factory(Status, data.status_final)
        status.statustype = factory(StatusType, data.status_type_final)

        zaak.status = status

        zaak_url = reverse(
            "cases:case_detail",
            kwargs={"object_id": str(zaak.uuid), "api_group_id": self.api_group.id},
        )

        # mock `_format_zaak_identificatie`, but then continue with result of actual call
        # (test redirect for invalid BSN that passes pattern validation)
        ret_val = zaak._format_zaak_identificatie()
        with mock.patch.object(
            Zaak, "_format_zaak_identificatie"
        ) as format_identificatie:
            format_identificatie.return_value = ret_val
            send_case_update_email(
                user,
                zaak,
                "case_status_notification",
                status=status,
                api_group=self.api_group,
            )

        format_identificatie.assert_called_once()

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [user.email])
        self.assertIn(config.name, email.subject)

        body_html = email.alternatives[0][0]
        self.assertIn(zaak.identificatie, body_html)
        self.assertIn(zaak.zaaktype.omschrijving, body_html)
        self.assertIn(status.statustype.statustekst, body_html)
        self.assertIn(zaak_url, body_html)
        self.assertIn(config.name, body_html)

    def test_send_case_update_email__no_status(self):
        config = SiteConfiguration.get_solo()
        data = MockAPIData()

        user = data.user_initiator

        zaak = factory(Zaak, data.zaak)
        zaak.zaaktype = factory(ZaakType, data.zaak_type)

        zaak_url = reverse(
            "cases:case_detail",
            kwargs={"object_id": str(zaak.uuid), "api_group_id": self.api_group.id},
        )

        send_case_update_email(
            user, zaak, "case_document_notification", api_group=self.api_group
        )

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [user.email])
        self.assertIn(config.name, email.subject)

        body_html = email.alternatives[0][0]
        self.assertIn(zaak.identificatie, body_html)
        self.assertIn(zaak.zaaktype.omschrijving, body_html)
        self.assertIn(zaak_url, body_html)
        self.assertIn(config.name, body_html)

    def test_get_nnp_initiator_nnp_id_from_roles(self):
        find_rol_1 = generate_rol(
            RolTypes.niet_natuurlijk_persoon,
            {"innNnpId": "100000001"},
            RolOmschrijving.initiator,
        )
        find_rol_2 = generate_rol(
            RolTypes.niet_natuurlijk_persoon,
            {"innNnpId": "100000002"},
            RolOmschrijving.medeinitiator,
        )
        roles = [
            find_rol_1,
            find_rol_2,
            # duplicate NNP ID
            generate_rol(
                RolTypes.niet_natuurlijk_persoon,
                {"innNnpId": "100000001"},
                RolOmschrijving.medeinitiator,
            ),
            # bad type
            generate_rol(
                RolTypes.natuurlijk_persoon,
                {"innNnpId": "404000001"},
                RolOmschrijving.initiator,
            ),
            # bad description
            generate_rol(
                RolTypes.niet_natuurlijk_persoon,
                {"innNnpId": "404000002"},
                RolOmschrijving.behandelaar,
            ),
            # bad identification
            generate_rol(
                RolTypes.niet_natuurlijk_persoon,
                {"not_the_expected_field": 123},
                RolOmschrijving.initiator,
            ),
        ]
        expected = {"100000001", "100000002"}
        actual = _get_nnp_initiator_nnp_id_from_roles(roles)
        self.assertEqual(set(actual), expected)

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
        actual = _get_np_initiator_bsns_from_roles(roles)
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
        check_roles = _get_np_initiator_bsns_from_roles(roles)
        expected_roles = {
            user_1.bsn,
            user_2.bsn,
            user_not_active.bsn,
        }
        self.assertEqual(set(check_roles), expected_roles)

        # of all the Users with Roles only these match all conditions
        expected = {user_1, user_2}
        actual = _get_initiator_users_from_roles(roles, api_group=self.api_group)

        self.assertEqual(set(actual), expected)

    def test_get_np_initiator_bsns_from_roles__limit_access_to_role(self):
        """When limit_access_to_role is set, only roles with that omschrijving are included."""
        initiator_rol = generate_rol(
            RolTypes.natuurlijk_persoon,
            {"inpBsn": "100000001"},
            RolOmschrijving.initiator,
        )
        medeinitiator_rol = generate_rol(
            RolTypes.natuurlijk_persoon,
            {"inpBsn": "100000002"},
            RolOmschrijving.medeinitiator,
        )
        roles = [initiator_rol, medeinitiator_rol]

        actual = _get_np_initiator_bsns_from_roles(
            roles, limit_access_to_role=ZaakBetrokkeneRol.initiator
        )

        self.assertEqual(actual, ["100000001"])

    def test_get_nnp_initiator_nnp_id_from_roles__limit_access_to_role(self):
        """When limit_access_to_role is set, only roles with that omschrijving are included."""
        initiator_rol = generate_rol(
            RolTypes.niet_natuurlijk_persoon,
            {"innNnpId": "100000001"},
            RolOmschrijving.initiator,
        )
        medeinitiator_rol = generate_rol(
            RolTypes.niet_natuurlijk_persoon,
            {"innNnpId": "100000002"},
            RolOmschrijving.medeinitiator,
        )
        roles = [initiator_rol, medeinitiator_rol]

        actual = _get_nnp_initiator_nnp_id_from_roles(
            roles, limit_access_to_role=ZaakBetrokkeneRol.initiator
        )

        self.assertEqual(actual, ["100000001"])

    def test_get_initiator_users_from_roles__limit_access_to_role(self):
        """When limit_access_to_role is set, medeinitiator users are excluded."""
        user_initiator = DigidUserFactory(bsn="100000001")
        user_medeinitiator = DigidUserFactory(bsn="100000002")

        roles = [
            generate_rol(
                RolTypes.natuurlijk_persoon,
                {"inpBsn": user_initiator.bsn},
                RolOmschrijving.initiator,
            ),
            generate_rol(
                RolTypes.natuurlijk_persoon,
                {"inpBsn": user_medeinitiator.bsn},
                RolOmschrijving.medeinitiator,
            ),
        ]

        actual = _get_initiator_users_from_roles(
            roles,
            api_group=self.api_group,
            limit_access_to_role=ZaakBetrokkeneRol.initiator,
        )

        self.assertEqual(actual, [user_initiator])
