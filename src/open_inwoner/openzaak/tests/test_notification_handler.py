import logging
from unittest.mock import Mock, patch

from django.test import TestCase

import requests_mock
from notifications_api_common.models import NotificationsConfig
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.constants import (
    RolOmschrijving,
    RolTypes,
    VertrouwelijkheidsAanduidingen,
)
from zgw_consumers.constants import APITypes
from zgw_consumers.test import generate_oas_component, mock_service_oas_get

from open_inwoner.accounts.tests.factories import DigidUserFactory, UserFactory
from open_inwoner.openzaak.notifications import (
    get_emailable_initiator_users_from_roles,
    get_np_initiator_bsns_from_roles,
    handle_zaken_notification,
)
from open_inwoner.openzaak.tests.factories import (
    NotificationFactory,
    ServiceFactory,
    SubscriptionFactory,
    generate_rol,
)

from ...utils.test import paginated_response
from ...utils.tests.helpers import AssertTimelineLogMixin, Lookups
from ..api_models import Status, StatusType, Zaak, ZaakType
from ..models import OpenZaakConfig
from .shared import CATALOGI_ROOT, DOCUMENTEN_ROOT, NOTIFICATIONS_ROOT, ZAKEN_ROOT


class NotificationHandlerTestCase(AssertTimelineLogMixin, TestCase):
    maxDiff = None
    config: OpenZaakConfig
    note_config: NotificationsConfig

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # services
        cls.zaak_service = ServiceFactory(api_root=ZAKEN_ROOT, api_type=APITypes.zrc)
        cls.catalogi_service = ServiceFactory(
            api_root=CATALOGI_ROOT, api_type=APITypes.ztc
        )
        cls.document_service = ServiceFactory(
            api_root=DOCUMENTEN_ROOT, api_type=APITypes.drc
        )
        cls.notifications_api_service = ServiceFactory(
            api_root=NOTIFICATIONS_ROOT, api_type=APITypes.nrc
        )
        # openzaak config
        cls.config = OpenZaakConfig.get_solo()
        cls.config.zaak_service = cls.zaak_service
        cls.config.catalogi_service = cls.catalogi_service
        cls.config.document_service = cls.document_service
        cls.config.save()

        cls.note_config = NotificationsConfig.get_solo()
        cls.note_config.notifications_api_service = cls.notifications_api_service
        cls.note_config.save()

        cls.subscription = SubscriptionFactory(client_id="foo_client_id")

    def _setUpOASMocks(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        mock_service_oas_get(m, DOCUMENTEN_ROOT, "drc")
        mock_service_oas_get(m, NOTIFICATIONS_ROOT, "nrc")

    def _setUpMocks(self, m):
        self._setUpOASMocks(m)

        # users with bsn
        self.user_initiator = DigidUserFactory(
            bsn="100000001",
            email="initiator@example.com",
        )
        self.zaak_type = generate_oas_component(
            "ztc",
            "schemas/ZaakType",
            url=f"{ZAKEN_ROOT}zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            catalogus=f"{CATALOGI_ROOT}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        )
        self.status_type_new = generate_oas_component(
            "ztc",
            "schemas/StatusType",
            url=f"{CATALOGI_ROOT}statustypen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            zaaktype=self.zaak_type["url"],
            informeren=True,
        )
        self.zaak = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            zaaktype=self.zaak_type["url"],
            status=f"{ZAKEN_ROOT}statussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            resultaat=f"{ZAKEN_ROOT}resultaten/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.status_new = generate_oas_component(
            "zrc",
            "schemas/Status",
            url=f"{ZAKEN_ROOT}statussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            zaak=self.zaak["url"],
            statustype=self.status_type_new["url"],
        )

        self.role_initiator = generate_oas_component(
            "zrc",
            "schemas/Rol",
            url=f"{ZAKEN_ROOT}rollen/aaaaaaaa-0001-aaaa-aaaa-aaaaaaaaaaaa",
            omschrijvingGeneriek=RolOmschrijving.initiator,
            betrokkeneType=RolTypes.natuurlijk_persoon,
            betrokkeneIdentificatie={
                "inpBsn": self.user_initiator.bsn,
            },
        )

        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}",
            json=paginated_response([self.role_initiator]),
        )
        for resource in [
            self.zaak,
            self.zaak_type,
            self.status_new,
            self.status_type_new,
        ]:
            m.get(resource["url"], json=resource)

    @requests_mock.Mocker()
    @patch("open_inwoner.openzaak.notifications.handle_status_update")
    def test_handle_zaken_notification_calls_handle_status_update(
        self, m, mock_handle: Mock
    ):
        self._setUpMocks(m)

        notification_status_update = NotificationFactory(
            resource="status",
            actie="update",
            resource_url=self.status_new["url"],
            hoofd_object=self.zaak["url"],
        )

        handle_zaken_notification(notification_status_update)

        mock_handle.assert_called_once()

        # check call arguments
        zaak = factory(Zaak, self.zaak)
        zaak.zaaktype = factory(ZaakType, self.zaak_type)
        status_new = factory(Status, self.status_new)
        status_new.statustype = factory(StatusType, self.status_type_new)

        self.assertEqual(self.user_initiator, mock_handle.call_args.args[0])
        self.assertEqual(zaak, mock_handle.call_args.args[1])
        self.assertEqual(status_new, mock_handle.call_args.args[2])

        self.assertTimelineLog(
            "accepted notification: informing users ",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )


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
        # users we're interested in
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
            RolOmschrijving.medeinitiator,
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
