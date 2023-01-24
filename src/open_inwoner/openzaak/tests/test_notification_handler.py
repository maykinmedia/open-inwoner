import logging
from typing import List, Optional
from unittest.mock import Mock, patch

from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils.formats import date_format

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
    send_status_update_email,
)
from open_inwoner.openzaak.tests.factories import (
    NotificationFactory,
    ServiceFactory,
    ZaakTypeConfigFactory,
    generate_rol,
)

from ...configurations.models import SiteConfiguration
from ...utils.test import ClearCachesMixin, paginated_response
from ...utils.tests.helpers import AssertTimelineLogMixin, Lookups
from ..api_models import Status, StatusType, Zaak, ZaakType
from ..models import OpenZaakConfig
from .shared import CATALOGI_ROOT, DOCUMENTEN_ROOT, ZAKEN_ROOT


class MockAPIData:
    """
    initializes isolated and valid data for a complete mock-request API flow,
        allows to manipulate data per test to break it,
        and still get dry/readable access to the data for assertions

    usage:

    data = MockAPIData()

    # change some resources
    data.zaak["some_field"] = "a different value"

    # install to your @requests_mock.Mocker()
    data.install_mocks(m)

    # install but return 404 for some resource
    data.install_mocks(m, res404=["zaak"])

    """

    def __init__(self):
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
            identificatie="My Zaaktype",
        )
        self.status_type = generate_oas_component(
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
        self.status = generate_oas_component(
            "zrc",
            "schemas/Status",
            url=f"{ZAKEN_ROOT}statussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            zaak=self.zaak["url"],
            statustype=self.status_type["url"],
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

        self.case_roles = [self.role_initiator]

        self.notification = NotificationFactory(
            resource="status",
            actie="update",
            resource_url=self.status["url"],
            hoofd_object=self.zaak["url"],
        )

    def setUpOASMocks(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")

    def install_mocks(self, m, *, res404: Optional[List[str]] = None) -> "MockData":
        self.setUpOASMocks(m)
        if res404 is None:
            res404 = []
        for attr in res404:
            if not hasattr(self, attr):
                raise Exception("configuration error")

        if "case_roles" in res404:
            m.get(
                f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}",
                status_code=404,
            )
        else:
            m.get(
                f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}",
                json=paginated_response(self.case_roles),
            )

        for resource_attr in [
            "zaak",
            "zaak_type",
            "status",
            "status_type",
        ]:
            resource = getattr(self, resource_attr)
            if resource_attr in res404:
                m.get(resource["url"], status_code=404)
            else:
                m.get(resource["url"], json=resource)

        return self


@requests_mock.Mocker()
@patch("open_inwoner.openzaak.notifications.handle_status_update")
class NotificationHandlerTestCase(AssertTimelineLogMixin, ClearCachesMixin, TestCase):
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
        # openzaak config
        cls.config = OpenZaakConfig.get_solo()
        cls.config.zaak_service = cls.zaak_service
        cls.config.catalogi_service = cls.catalogi_service
        cls.config.document_service = cls.document_service
        cls.config.zaak_max_confidentiality = VertrouwelijkheidsAanduidingen.openbaar
        cls.config.save()

    def test_handle_zaken_notification_calls_handle_status_update(
        self, m, mock_handle: Mock
    ):
        data = MockAPIData().install_mocks(m)

        handle_zaken_notification(data.notification)

        history = m.request_history

        mock_handle.assert_called_once()

        # check call arguments
        args = mock_handle.call_args.args
        self.assertEqual(args[0], data.user_initiator)
        self.assertEqual(args[1].url, data.zaak["url"])
        self.assertEqual(args[2].url, data.status["url"])

        self.assertTimelineLog(
            "accepted notification: informing users ",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    def test_bails_when_bad_notification_channel(self, m, mock_handle: Mock):
        notification = NotificationFactory(kanaal="not_zaken")
        with self.assertRaisesRegex(
            Exception, r"^handler expects kanaal 'zaken' but received 'not_zaken'"
        ):
            handle_zaken_notification(notification)

        mock_handle.assert_not_called()

    def test_bails_when_bad_notification_resource(self, m, mock_handle: Mock):
        notification = NotificationFactory(resource="not_status")

        handle_zaken_notification(notification)

        self.assertTimelineLog(
            "ignored notification: resource is not 'status' but 'not_status' for case https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )
        mock_handle.assert_not_called()

    def test_bails_when_no_roles_found_for_case(self, m, mock_handle: Mock):
        data = MockAPIData()
        data.install_mocks(m, res404=["case_roles"])

        handle_zaken_notification(data.notification)

        self.assertTimelineLog(
            "ignored notification: cannot retrieve rollen for case https://",
            lookup=Lookups.startswith,
            level=logging.ERROR,
        )
        mock_handle.assert_not_called()

    def test_bails_when_no_emailable_users_are_found_for_roles(
        self, m, mock_handle: Mock
    ):
        data = MockAPIData()
        data.user_initiator.delete()
        data.install_mocks(m)

        handle_zaken_notification(data.notification)

        self.assertTimelineLog(
            "ignored notification: no users with bsn and valid email as (mede)initiators in case https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )
        mock_handle.assert_not_called()

    def test_bails_when_cannot_fetch_status(self, m, mock_handle: Mock):
        data = MockAPIData()
        data.install_mocks(m, res404=["status"])

        handle_zaken_notification(data.notification)

        self.assertTimelineLog(
            f"ignored notification: cannot retrieve status {data.status['url']} for case https://",
            lookup=Lookups.startswith,
            level=logging.ERROR,
        )
        mock_handle.assert_not_called()

    def test_bails_when_cannot_fetch_status_type(self, m, mock_handle: Mock):
        data = MockAPIData()
        data.install_mocks(m, res404=["status_type"])

        handle_zaken_notification(data.notification)

        self.assertTimelineLog(
            f"ignored notification: cannot retrieve status_type {data.status_type['url']} for case https://",
            lookup=Lookups.startswith,
            level=logging.ERROR,
        )
        mock_handle.assert_not_called()

    def test_bails_when_status_type_not_marked_as_informeren(
        self, m, mock_handle: Mock
    ):
        data = MockAPIData()
        data.status_type["informeren"] = False
        data.install_mocks(m)

        handle_zaken_notification(data.notification)

        self.assertTimelineLog(
            f"ignored notification: status_type.informeren is false for status {data.status['url']} and case https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )
        mock_handle.assert_not_called()

    def test_bails_when_cannot_fetch_case(self, m, mock_handle: Mock):
        data = MockAPIData()
        data.install_mocks(m, res404=["zaak"])

        handle_zaken_notification(data.notification)

        self.assertTimelineLog(
            f"ignored notification: cannot retrieve case https://",
            lookup=Lookups.startswith,
            level=logging.ERROR,
        )
        mock_handle.assert_not_called()

    def test_bails_when_cannot_fetch_case_type(self, m, mock_handle: Mock):
        data = MockAPIData()
        data.install_mocks(m, res404=["zaak_type"])

        handle_zaken_notification(data.notification)

        self.assertTimelineLog(
            f"ignored notification: cannot retrieve case_type https://",
            lookup=Lookups.startswith,
            level=logging.ERROR,
        )
        mock_handle.assert_not_called()

    def test_bails_when_case_not_visible_confidentiality(self, m, mock_handle: Mock):
        data = MockAPIData()
        data.zaak["vertrouwelijkheidaanduiding"] = VertrouwelijkheidsAanduidingen.geheim
        data.install_mocks(m)

        handle_zaken_notification(data.notification)

        self.assertTimelineLog(
            f"ignored notification: bad confidentiality 'geheim' for case https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )
        mock_handle.assert_not_called()

    def test_bails_when_skip_notication_statustype_informeren_is_set_and_no_zaaktypeconfig_is_found(
        self, m, mock_handle: Mock
    ):
        oz_config = OpenZaakConfig.get_solo()
        oz_config.skip_notication_statustype_informeren = True
        oz_config.save()

        data = MockAPIData()
        data.install_mocks(m)

        handle_zaken_notification(data.notification)

        self.assertTimelineLog(
            f"ignored notification: 'skip_notication_statustype_informeren' is True but cannot retrieve case_type configuration '{data.zaak_type['identificatie']}' for case https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )
        mock_handle.assert_not_called()

    def test_handle_notification_when_skip_notication_statustype_informeren_is_set_and_zaaktypeconfig_is_found(
        self, m, mock_handle: Mock
    ):
        oz_config = OpenZaakConfig.get_solo()
        oz_config.skip_notication_statustype_informeren = True
        oz_config.save()

        data = MockAPIData().install_mocks(m)

        ZaakTypeConfigFactory.create(
            catalogus__url=data.zaak_type["catalogus"],
            identificatie=data.zaak_type["identificatie"],
            # set this to notify
            notify_status_changes=True,
        )

        handle_zaken_notification(data.notification)

        history = m.request_history

        mock_handle.assert_called_once()

        # check call arguments
        args = mock_handle.call_args.args
        self.assertEqual(args[0], data.user_initiator)
        self.assertEqual(args[1].url, data.zaak["url"])
        self.assertEqual(args[2].url, data.status["url"])

        self.assertTimelineLog(
            "accepted notification: informing users ",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    def test_bails_when_skip_notication_statustype_informeren_is_set_and_zaaktypeconfig_is_found_but_not_set(
        self, m, mock_handle: Mock
    ):
        oz_config = OpenZaakConfig.get_solo()
        oz_config.skip_notication_statustype_informeren = True
        oz_config.save()

        data = MockAPIData()
        data.install_mocks(m)

        ZaakTypeConfigFactory.create(
            catalogus__url=data.zaak_type["catalogus"],
            identificatie=data.zaak_type["identificatie"],
            notify_status_changes=False,
        )

        handle_zaken_notification(data.notification)

        self.assertTimelineLog(
            f"ignored notification: case_type configuration '{data.zaak_type['identificatie']}' found but 'notify_status_changes' is False for case https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )
        mock_handle.assert_not_called()

    def test_bails_when_skip_notication_statustype_informeren_is_set_and_zaaktypeconfig_is_not_found_because_different_catalog(
        self, m, mock_handle: Mock
    ):
        oz_config = OpenZaakConfig.get_solo()
        oz_config.skip_notication_statustype_informeren = True
        oz_config.save()

        data = MockAPIData()
        data.install_mocks(m)

        ZaakTypeConfigFactory.create(
            catalogus__url="http://not-the-catalogus.xyz",
            identificatie=data.zaak_type["identificatie"],
            notify_status_changes=False,
        )

        handle_zaken_notification(data.notification)

        self.assertTimelineLog(
            f"ignored notification: 'skip_notication_statustype_informeren' is True but cannot retrieve case_type configuration '{data.zaak_type['identificatie']}' for case https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )
        mock_handle.assert_not_called()


class NotificationHandlerEmailTestCase(TestCase):
    def test_send_status_update_email(self):
        config = SiteConfiguration.get_solo()
        data = MockAPIData()

        user = data.user_initiator

        case = factory(Zaak, data.zaak)
        case.zaaktype = factory(ZaakType, data.zaak_type)

        status = factory(Status, data.status)
        status.statustype = factory(StatusType, data.status_type)

        case_url = reverse("accounts:case_status", kwargs={"object_id": str(case.uuid)})

        send_status_update_email(user, case, status)

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
