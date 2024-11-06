import datetime
import hashlib
import random
import uuid
from unittest.mock import patch
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.test import TransactionTestCase
from django.test.utils import override_settings
from django.urls import reverse_lazy

import requests_mock
from django_webtest import TransactionWebTest
from furl import furl
from pyquery import PyQuery as PQ
from timeline_logger.models import TimelineLog
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.tests.factories import UserFactory, eHerkenningUserFactory
from open_inwoner.cms.cases.views.cases import CaseFilterFormOption, InnerCaseListView
from open_inwoner.utils.test import (
    ClearCachesMixin,
    paginated_response,
    set_kvk_branch_number_in_session,
)
from open_inwoner.utils.tests.helpers import AssertTimelineLogMixin, Lookups

from ...utils.tests.helpers import AssertRedirectsMixin
from ..api_models import Zaak
from ..constants import StatusIndicators
from ..models import OpenZaakConfig
from .factories import (
    CatalogusConfigFactory,
    ZaakTypeConfigFactory,
    ZaakTypeStatusTypeConfigFactory,
    ZGWApiGroupConfigFactory,
)
from .helpers import generate_oas_component_cached
from .mocks import ESuiteSubmissionData
from .shared import (
    ANOTHER_CATALOGI_ROOT,
    ANOTHER_FORMS_ROOT,
    ANOTHER_ZAKEN_ROOT,
    CATALOGI_ROOT,
    FORMS_ROOT,
    ZAKEN_ROOT,
)


class SeededUUIDGenerator:
    def __init__(self, seed_value):
        self.rng = random.Random(seed_value)
        self.current_uuid = self._generate_initial_uuid()

    def _generate_initial_uuid(self):
        random_bytes = [self.rng.randint(0, 255) for _ in range(16)]
        return uuid.UUID(bytes=bytes(random_bytes), version=4)

    def get_uuid(self):
        # Increment the UUID
        int_value = int(self.current_uuid)
        int_value += 1
        self.current_uuid = uuid.UUID(int=int_value, version=4)
        return self.current_uuid


def _md5(value: str):
    m = hashlib.md5()
    m.update(value.encode("utf-8"))
    return m.hexdigest()


# Avoid redirects through `KvKLoginMiddleware`
PATCHED_MIDDLEWARE = [
    m
    for m in settings.MIDDLEWARE
    if m != "open_inwoner.kvk.middleware.KvKLoginMiddleware"
]


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class CaseListAccessTests(AssertRedirectsMixin, ClearCachesMixin, TransactionWebTest):
    outer_url = reverse_lazy("cases:index")
    inner_url = reverse_lazy("cases:cases_content")

    def setUp(self):
        super().setUp()

        # services
        ZGWApiGroupConfigFactory(
            ztc_service__api_root=CATALOGI_ROOT,
            zrc_service__api_root=ZAKEN_ROOT,
            form_service=None,
        )

    def test_user_access_is_forbidden_when_not_logged_in_via_digid(self):
        # User's bsn is None when logged in by email (default method)
        user = UserFactory(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.default,
        )
        self.app.get(self.outer_url, user=user, status=403)

    def test_anonymous_user_has_no_access_to_cases_page(self):
        user = AnonymousUser()

        response = self.app.get(self.outer_url, user=user)

        self.assertRedirectsLogin(response, next=self.outer_url)

    def test_bad_request_when_no_htmx_in_inner_urls(self):
        user = UserFactory(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.default,
        )

        self.app.get(self.inner_url, user=user, status=400)

    @requests_mock.Mocker()
    def test_no_cases_are_retrieved_when_http_404(self, m):
        user = UserFactory(
            login_type=LoginTypeChoices.digid, bsn="900222086", email="john@smith.nl"
        )
        m.get(
            f"{ZAKEN_ROOT}zaken?rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn=900222086",
            status_code=404,
        )

        response = self.app.get(
            self.inner_url, user=user, headers={"HX-Request": "true"}
        )

        self.assertListEqual(response.context.get("cases"), [])

    @requests_mock.Mocker()
    def test_no_cases_are_retrieved_when_http_500(self, m):
        user = UserFactory(
            login_type=LoginTypeChoices.digid, bsn="900222086", email="john@smith.nl"
        )
        m.get(
            f"{ZAKEN_ROOT}zaken?rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn=900222086",
            status_code=500,
        )

        response = self.app.get(
            self.inner_url, user=user, headers={"HX-Request": "true"}
        )

        self.assertListEqual(response.context.get("cases"), [])


class CaseListMocks:
    def __init__(self, *, zaken_root: str, catalogi_root: str, user, eherkenning_user):
        self.zaken_root = zaken_root
        self.catalogi_root = catalogi_root
        self.user = user
        self.eherkenning_user = eherkenning_user
        uuid_generator = SeededUUIDGenerator(zaken_root + catalogi_root)

        catalogus_url = f"{catalogi_root}catalogussen/{uuid_generator.get_uuid()}"

        self.zaaktype = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            url=f"{catalogi_root}zaaktypen/{uuid_generator.get_uuid()}",
            omschrijving="Applying for a cup of coffee",
            identificatie=f"ZAAK-2022-{_md5(zaken_root)}",
            catalogus=catalogus_url,
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            indicatieInternOfExtern="extern",
        )
        self.zaak_type_intern = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            url=f"{catalogi_root}zaaktypen/{uuid_generator.get_uuid()}",
            omschrijving="Applying for an internal cup of coffee for employees",
            catalogus=catalogus_url,
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            indicatieInternOfExtern="intern",
        )

        initial_statustype_id = str(uuid_generator.get_uuid())
        self.status_type_initial = generate_oas_component_cached(
            "ztc",
            "schemas/StatusType",
            uuid=initial_statustype_id,
            url=f"{catalogi_root}statustypen/{initial_statustype_id}",
            zaaktype=self.zaaktype["url"],
            omschrijving="Initial request",
            statustekst="",
            volgnummer=1,
            isEindstatus=False,
        )
        statustype_finish_id = str(uuid_generator.get_uuid())
        self.status_type_finish = generate_oas_component_cached(
            "ztc",
            "schemas/StatusType",
            uuid=statustype_finish_id,
            url=f"{catalogi_root}statustypen/{statustype_finish_id}",
            zaaktype=self.zaaktype["url"],
            omschrijving="Finish",
            statustekst="Statustekst finish",
            volgnummer=2,
            isEindstatus=True,
        )
        resultaat_type_id = str(uuid_generator.get_uuid())
        self.resultaat_type = generate_oas_component_cached(
            "ztc",
            "schemas/ResultaatType",
            uuid=resultaat_type_id,
            url=f"{catalogi_root}resultaattypen/{resultaat_type_id}",
            zaaktype=self.zaaktype["url"],
            omschrijving="Eindresultaat",
            resultaattypeomschrijving="test1",
            selectielijstklasse="ABC",
        )

        self.catalogus_config = CatalogusConfigFactory.create(
            url=self.zaaktype["catalogus"]
        )
        self.zaaktype_config1 = ZaakTypeConfigFactory.create(
            urls=[self.zaaktype["url"]],
            identificatie=self.zaaktype["identificatie"],
            catalogus=self.catalogus_config,
        )
        self.zt_statustype_config1 = ZaakTypeStatusTypeConfigFactory.create(
            zaaktype_config=self.zaaktype_config1,
            statustype_url=self.status_type_initial["url"],
            status_indicator=StatusIndicators.warning,
            status_indicator_text="U moet documenten toevoegen",
            description="Lorem ipsum dolor sit amet",
            call_to_action_url="https://example.com",
            call_to_action_text="Click me",
        )
        # open
        zaak1_id = str(uuid_generator.get_uuid())
        self.zaak1 = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            url=f"{zaken_root}zaken/{zaak1_id}",
            uuid=zaak1_id,
            zaaktype=self.zaaktype["url"],
            identificatie=f"ZAAK-2022-{_md5(zaak1_id)}",
            omschrijving="Coffee zaak 1",
            startdatum="2022-01-02",
            einddatum=None,
            status=f"{zaken_root}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.status1 = generate_oas_component_cached(
            "zrc",
            "schemas/Status",
            url=self.zaak1["status"],
            zaak=self.zaak1["url"],
            statustype=self.status_type_initial["url"],
            datumStatusGezet="2021-01-12",
            statustoelichting="",
        )
        self.zaak2 = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            url=f"{zaken_root}zaken/e4d469b9-6666-4bdd-bf42-b53445298102",
            uuid="e4d469b9-6666-4bdd-bf42-b53445298102",
            zaaktype=self.zaaktype["url"],
            identificatie="0014ESUITE66392022",
            omschrijving="Coffee zaak 2",
            startdatum="2022-01-12",
            einddatum=None,
            status=f"{zaken_root}statussen/3da81560-c7fc-476a-ad13-beu760sle929",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.status2 = generate_oas_component_cached(
            "zrc",
            "schemas/Status",
            url=self.zaak2["status"],
            zaak=self.zaak2["url"],
            statustype=self.status_type_initial["url"],
            datumStatusGezet="2021-03-12",
            statustoelichting="",
        )

        self.zaak_result = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            url=f"{zaken_root}zaken/e4d469b9-6666-4bdd-bf42-b53445298123",
            uuid="e4d469b9-6666-4bdd-bf42-b53445298123",
            zaaktype=self.zaaktype["url"],
            identificatie="0014ESUITE43212022",
            omschrijving="Result zaak",
            startdatum="2020-01-01",
            einddatum="2022-01-13",
            status=f"{zaken_root}statussen/3da81560-c7fc-476a-ad13-beu760sle929",
            resultaat=f"{zaken_root}resultaten/3da81560-c7fc-476a-ad13-beu760sle929",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.result = generate_oas_component_cached(
            "zrc",
            "schemas/Resultaat",
            uuid="a44153aa-ad2c-6a07-be75-15add5113",
            url=self.zaak_result["resultaat"],
            resultaattype=self.resultaat_type["url"],
            zaak=self.zaak_result["url"],
            toelichting="resultaat toelichting",
        )

        self.zaak_eherkenning1 = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            url=f"{zaken_root}zaken/bf558d78-280d-4723-b8e8-2b6179cd74e3",
            uuid="bf558d78-280d-4723-b8e8-2b6179cd74e3",
            zaaktype=self.zaaktype["url"],
            identificatie="ZAAK-2022-0000000003",
            omschrijving="Coffee zaak 3",
            startdatum="2022-01-02",
            einddatum=None,
            status=f"{zaken_root}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.zaak_eherkenning2 = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            url=f"{zaken_root}zaken/ff5026c8-5d1f-4bd2-a069-58d4bf75ec8c",
            uuid="ff5026c8-5d1f-4bd2-a069-58d4bf75ec8c",
            zaaktype=self.zaaktype["url"],
            identificatie="ZAAK-2022-0000000004",
            omschrijving="Coffee zaak 4",
            startdatum="2022-02-02",
            einddatum=None,
            status=f"{zaken_root}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        # closed
        self.zaak3 = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            url=f"{zaken_root}zaken/6f8de38f-85ea-42d3-978c-845a033335a7",
            uuid="6f8de38f-85ea-42d3-978c-845a033335a7",
            zaaktype=self.zaaktype["url"],
            identificatie="ZAAK-2022-0001000003",
            omschrijving="Coffee zaak closed",
            startdatum="2021-07-26",
            einddatum="2022-01-16",
            status=f"{zaken_root}statussen/98659876-bbb3-476a-ad13-n3nvcght758js",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.status3 = generate_oas_component_cached(
            "zrc",
            "schemas/Status",
            url=self.zaak3["status"],
            zaak=self.zaak3["url"],
            statustype=self.status_type_finish["url"],
            datumStatusGezet="2021-03-15",
            statustoelichting="",
        )
        # not visible
        zaak_intern_id = str(uuid_generator.get_uuid())
        self.zaak_intern = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            url=f"{zaken_root}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4ee0bf67d",
            uuid="d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            zaaktype=self.zaak_type_intern["url"],
            identificatie="ZAAK-2022-0000000009",
            omschrijving="Intern zaak",
            startdatum="2022-01-02",
            einddatum=None,
            status=f"{zaken_root}statussen/3da89990-c7fc-476a-ad13-c90234500333",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.status_intern = generate_oas_component_cached(
            "zrc",
            "schemas/Status",
            url=self.zaak_intern["status"],
            zaak=self.zaak_intern["url"],
            statustype=self.status_type_initial["url"],
            datumStatusGezet="2021-01-12",
            statustoelichting="",
        )
        self.submission = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            url=f"{zaken_root}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4ee0bf67d",
            uuid="c8yudeb7-490f-2cw9-h8wa-44h9830bf67d",
            naam="mysub",
            datum_laatste_wijziging="2023-10-10",
        )

    def _setUpMocks(self, m):
        m.get(
            furl(f"{self.zaken_root}zaken")
            .add(
                {
                    "rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn": self.user.bsn,
                    "maximaleVertrouwelijkheidaanduiding": VertrouwelijkheidsAanduidingen.beperkt_openbaar,
                }
            )
            .url,
            json=paginated_response(
                [self.zaak1, self.zaak2, self.zaak3, self.zaak_intern, self.zaak_result]
            ),
        )
        for identifier in [self.eherkenning_user.kvk, self.eherkenning_user.rsin]:
            m.get(
                furl(f"{self.zaken_root}zaken")
                .add(
                    {
                        "rol__betrokkeneIdentificatie__nietNatuurlijkPersoon__innNnpId": identifier,
                        "maximaleVertrouwelijkheidaanduiding": VertrouwelijkheidsAanduidingen.beperkt_openbaar,
                    }
                )
                .url,
                json=paginated_response(
                    [self.zaak_eherkenning1, self.zaak_eherkenning2]
                ),
            )
            m.get(
                furl(f"{self.zaken_root}zaken")
                .add(
                    {
                        "maximaleVertrouwelijkheidaanduiding": VertrouwelijkheidsAanduidingen.beperkt_openbaar,
                        "rol__betrokkeneIdentificatie__vestiging__vestigingsNummer": "1234",
                    }
                )
                .url,
                json=paginated_response([self.zaak_eherkenning1]),
            )
        for resource in [
            self.zaaktype,
            self.status_type_initial,
            self.status_type_finish,
            self.resultaat_type,
            self.result,
            self.status1,
            self.status2,
            self.status3,
            self.zaak_intern,
            self.status_intern,
            self.zaak_type_intern,
        ]:
            m.get(resource["url"], json=resource)


@requests_mock.Mocker()
@override_settings(
    ROOT_URLCONF="open_inwoner.cms.tests.urls",
    MIDDLEWARE=PATCHED_MIDDLEWARE,
)
class CaseListViewTests(AssertTimelineLogMixin, ClearCachesMixin, TransactionTestCase):
    inner_url = reverse_lazy("cases:cases_content")
    maxDiff = None

    def setUp(self):
        super().setUp()

        self.user = UserFactory(
            login_type=LoginTypeChoices.digid, bsn="900222086", email="johm@smith.nl"
        )
        self.eherkenning_user = eHerkenningUserFactory.create(
            kvk="12345678",
            rsin="123456789",
            login_type=LoginTypeChoices.eherkenning,
        )

        # openzaak config
        self.config = OpenZaakConfig.get_solo()
        self.config.zaak_max_confidentiality = (
            VertrouwelijkheidsAanduidingen.beperkt_openbaar
        )
        self.config.save()

        # services
        self.mocks = []
        self.roots = (
            (ZAKEN_ROOT, CATALOGI_ROOT),
            (ANOTHER_ZAKEN_ROOT, ANOTHER_CATALOGI_ROOT),
        )
        self.api_groups = []
        for zaken_root, catalogi_root in self.roots:
            self.api_groups.append(
                ZGWApiGroupConfigFactory(
                    zrc_service__api_root=zaken_root,
                    ztc_service__api_root=catalogi_root,
                    form_service=None,
                )
            )
            self.mocks.append(
                CaseListMocks(
                    zaken_root=zaken_root,
                    catalogi_root=catalogi_root,
                    user=self.user,
                    eherkenning_user=self.eherkenning_user,
                )
            )

    def test_list_cases(self, m):
        for mock in self.mocks:
            mock._setUpMocks(m)

        # Added for https://taiga.maykinmedia.nl/project/open-inwoner/task/1904
        # In eSuite it is possible to reuse a StatusType for multiple ZaakTypen, which
        # led to errors when retrieving the ZaakTypeStatusTypeConfig. This duplicate
        # config is added to verify that that issue was solved
        for mock in self.mocks:
            ZaakTypeStatusTypeConfigFactory.create(
                statustype_url=mock.status_type_initial["url"],
                status_indicator=StatusIndicators.warning,
                status_indicator_text="U moet documenten toevoegen",
                description="Lorem ipsum dolor sit amet",
                call_to_action_url="https://example.com",
                call_to_action_text="duplicate",
            )

        self.client.force_login(user=self.user)
        response = self.client.get(self.inner_url, HTTP_HX_REQUEST="true")

        expected_cases = []
        for i, mock in enumerate(self.mocks):
            expected_cases.extend(
                [
                    {
                        "uuid": mock.zaak2["uuid"],
                        "start_date": datetime.date.fromisoformat(
                            mock.zaak2["startdatum"]
                        ),
                        "end_date": None,
                        "identification": mock.zaak2["identificatie"],
                        "description": mock.zaaktype["omschrijving"],
                        "current_status": mock.status_type_initial["omschrijving"],
                        "zaaktype_config": mock.zaaktype_config1,
                        "statustype_config": mock.zt_statustype_config1,
                        "case_type": "Zaak",
                        "api_group": self.api_groups[i],
                    },
                    {
                        "uuid": mock.zaak1["uuid"],
                        "start_date": datetime.date.fromisoformat(
                            mock.zaak1["startdatum"]
                        ),
                        "end_date": None,
                        "identification": mock.zaak1["identificatie"],
                        "description": mock.zaaktype["omschrijving"],
                        "current_status": mock.status_type_initial["omschrijving"],
                        "zaaktype_config": mock.zaaktype_config1,
                        "statustype_config": mock.zt_statustype_config1,
                        "case_type": "Zaak",
                        "api_group": self.api_groups[i],
                    },
                    {
                        "uuid": mock.zaak3["uuid"],
                        "start_date": datetime.date.fromisoformat(
                            mock.zaak3["startdatum"]
                        ),
                        "end_date": datetime.date.fromisoformat(
                            mock.zaak3["einddatum"]
                        ),
                        "identification": mock.zaak3["identificatie"],
                        "description": mock.zaaktype["omschrijving"],
                        "current_status": mock.status_type_finish["statustekst"],
                        "zaaktype_config": mock.zaaktype_config1,
                        "statustype_config": None,
                        "case_type": "Zaak",
                        "api_group": self.api_groups[i],
                    },
                    {
                        "uuid": mock.zaak_result["uuid"],
                        "start_date": datetime.date.fromisoformat(
                            mock.zaak_result["startdatum"]
                        ),
                        "end_date": datetime.date(2022, 1, 13),
                        "identification": mock.zaak_result["identificatie"],
                        "description": mock.zaaktype["omschrijving"],
                        # use result here
                        "current_status": mock.resultaat_type["omschrijving"],
                        "zaaktype_config": mock.zaaktype_config1,
                        "statustype_config": mock.zt_statustype_config1,
                        "case_type": "Zaak",
                        "api_group": self.api_groups[i],
                    },
                ]
            )

        self.assertListEqual(response.context["cases"], expected_cases)
        # don't show internal cases
        for mock in self.mocks:
            self.assertNotContains(response, mock.zaak_intern["omschrijving"])
            self.assertNotContains(response, text=mock.zaak_intern["identificatie"])

        # check zaken request query parameters
        for zaken_root in ("zaken.nl", "andere-zaken.nl"):
            list_zaken_req = [
                req
                for req in m.request_history
                if req.hostname == zaken_root and req.path == "/api/v1/zaken"
            ][0]
            self.assertEqual(len(list_zaken_req.qs), 2)
            self.assertEqual(
                list_zaken_req.qs,
                {
                    "rol__betrokkeneidentificatie__natuurlijkpersoon__inpbsn": [
                        self.user.bsn
                    ],
                    "maximalevertrouwelijkheidaanduiding": [
                        VertrouwelijkheidsAanduidingen.beperkt_openbaar
                    ],
                },
            )

        # case filter form is disabled by default
        self.assertFalse(response.context.get("filter_form_enabled"))

    def test_filter_widget_is_controlled_by_zaken_filter_enabled(self, m):
        self.client.force_login(user=self.user)

        for flag in True, False:
            with self.subTest(f"zaken_filter_enabled={flag}"):
                self.config.zaken_filter_enabled = flag
                self.config.save()

                response = self.client.get(self.inner_url, HTTP_HX_REQUEST="true")

                self.assertEqual(response.context.get("filter_form_enabled"), flag)

                doc = PQ(response.rendered_content)
                self.assertEqual(len(doc.find("#filterBar")), 1 if flag else 0)

    @staticmethod
    def _encode_statuses(
        status_or_statuses: CaseFilterFormOption | list[CaseFilterFormOption],
    ):
        statuses = (
            [status_or_statuses]
            if isinstance(status_or_statuses, CaseFilterFormOption)
            else status_or_statuses
        )
        parts = [urlencode({"status": status.value}) for status in statuses]
        return "&".join(parts)

    def test_filter_cases_simple(self, m):
        for mock in self.mocks:
            mock._setUpMocks(m)

        self.config.zaken_filter_enabled = True
        self.config.save()

        self.client.force_login(user=self.user)
        inner_url = f"{reverse_lazy('cases:cases_content')}?{self._encode_statuses(CaseFilterFormOption.OPEN_CASE)}"

        response = self.client.get(inner_url, HTTP_HX_REQUEST="true")

        # check cases
        cases = response.context["cases"]

        self.assertEqual(len(cases), 4)
        for case in cases:
            self.assertIsNone(case["end_date"])

    def test_filter_cases_multiple(self, m):
        for mock in self.mocks:
            mock._setUpMocks(m)

        self.config.zaken_filter_enabled = True
        self.config.save()

        self.client.force_login(user=self.user)
        filter_param = self._encode_statuses(
            [CaseFilterFormOption.CLOSED_CASE, CaseFilterFormOption.OPEN_SUBMISSION]
        )
        inner_url = f"{reverse_lazy('cases:cases_content')}?{filter_param}"

        response = self.client.get(inner_url, HTTP_HX_REQUEST="true")

        # check cases
        cases = response.context["cases"]

        self.assertEqual(len(cases), 4)
        for case in cases:
            self.assertIsNotNone(case["end_date"])

    @set_kvk_branch_number_in_session(None)
    def test_list_cases_for_eherkenning_user(self, m):
        for mock in self.mocks:
            mock._setUpMocks(m)

        for fetch_eherkenning_zaken_with_rsin in [True, False]:
            with self.subTest(
                fetch_eherkenning_zaken_with_rsin=fetch_eherkenning_zaken_with_rsin
            ):
                self.config.fetch_eherkenning_zaken_with_rsin = (
                    fetch_eherkenning_zaken_with_rsin
                )
                self.config.save()

                m.reset_mock()

                self.client.force_login(user=self.eherkenning_user)
                response = self.client.get(self.inner_url, HTTP_HX_REQUEST="true")

                expected_cases = []
                for i, mock in enumerate(self.mocks):
                    expected_cases.extend(
                        [
                            {
                                "uuid": mock.zaak_eherkenning2["uuid"],
                                "start_date": datetime.date.fromisoformat(
                                    mock.zaak_eherkenning2["startdatum"]
                                ),
                                "end_date": None,
                                "identification": mock.zaak_eherkenning2[
                                    "identificatie"
                                ],
                                "description": mock.zaaktype["omschrijving"],
                                "current_status": mock.status_type_initial[
                                    "omschrijving"
                                ],
                                "zaaktype_config": mock.zaaktype_config1,
                                "statustype_config": mock.zt_statustype_config1,
                                "case_type": "Zaak",
                                "api_group": self.api_groups[i],
                            },
                            {
                                "uuid": mock.zaak_eherkenning1["uuid"],
                                "start_date": datetime.date.fromisoformat(
                                    mock.zaak_eherkenning1["startdatum"]
                                ),
                                "end_date": None,
                                "identification": mock.zaak_eherkenning1[
                                    "identificatie"
                                ],
                                "description": mock.zaaktype["omschrijving"],
                                "current_status": mock.status_type_initial[
                                    "omschrijving"
                                ],
                                "zaaktype_config": mock.zaaktype_config1,
                                "statustype_config": mock.zt_statustype_config1,
                                "case_type": "Zaak",
                                "api_group": self.api_groups[i],
                            },
                        ]
                    )

                self.assertListEqual(response.context["cases"], expected_cases)

                for mock in self.mocks:
                    # don't show internal cases
                    self.assertNotContains(response, mock.zaak_intern["omschrijving"])
                    self.assertNotContains(response, mock.zaak_intern["identificatie"])

                # check zaken request query parameters
                for zaken_root in ("zaken.nl", "andere-zaken.nl"):
                    list_zaken_req = [
                        req
                        for req in m.request_history
                        if req.hostname == zaken_root and req.path == "/api/v1/zaken"
                    ][0]
                    identifier = (
                        self.eherkenning_user.rsin
                        if fetch_eherkenning_zaken_with_rsin
                        else self.eherkenning_user.kvk
                    )

                    self.assertEqual(len(list_zaken_req.qs), 2)
                    self.assertEqual(
                        list_zaken_req.qs,
                        {
                            "rol__betrokkeneidentificatie__nietnatuurlijkpersoon__innnnpid": [
                                identifier
                            ],
                            "maximalevertrouwelijkheidaanduiding": [
                                VertrouwelijkheidsAanduidingen.beperkt_openbaar
                            ],
                        },
                    )

    @set_kvk_branch_number_in_session("1234")
    def test_list_cases_for_eherkenning_user_with_vestigingsnummer(self, m):
        """
        If a KVK_BRANCH_NUMBER that is different from the KVK number is specified,
        additional filtering by vestiging should be applied when retrieving zaken
        """
        for mock in self.mocks:
            mock._setUpMocks(m)

        self.client.force_login(user=self.eherkenning_user)

        for fetch_eherkenning_zaken_with_rsin in [True, False]:
            with self.subTest(
                fetch_eherkenning_zaken_with_rsin=fetch_eherkenning_zaken_with_rsin
            ):
                self.config.fetch_eherkenning_zaken_with_rsin = (
                    fetch_eherkenning_zaken_with_rsin
                )
                self.config.save()

                m.reset_mock()

                response = self.client.get(self.inner_url, HTTP_HX_REQUEST="true")

                expected_cases = [
                    {
                        "uuid": mock.zaak_eherkenning1["uuid"],
                        "start_date": datetime.date.fromisoformat(
                            mock.zaak_eherkenning1["startdatum"]
                        ),
                        "end_date": None,
                        "identification": mock.zaak_eherkenning1["identificatie"],
                        "description": mock.zaaktype["omschrijving"],
                        "current_status": mock.status_type_initial["omschrijving"],
                        "zaaktype_config": mock.zaaktype_config1,
                        "statustype_config": mock.zt_statustype_config1,
                        "case_type": "Zaak",
                        "api_group": self.api_groups[i],
                    }
                    for i, mock in enumerate(self.mocks)
                ]
                self.assertListEqual(
                    response.context["cases"],
                    expected_cases,
                )
                for mock in self.mocks:
                    # don't show internal cases
                    self.assertNotContains(response, mock.zaak_intern["omschrijving"])
                    self.assertNotContains(response, mock.zaak_intern["identificatie"])

                # check zaken request query parameters
                for zaken_root in ("zaken.nl", "andere-zaken.nl"):
                    list_zaken_req = [
                        req
                        for req in m.request_history
                        if req.hostname == zaken_root and req.path == "/api/v1/zaken"
                    ][0]
                    identifier = (
                        self.eherkenning_user.rsin
                        if fetch_eherkenning_zaken_with_rsin
                        else self.eherkenning_user.kvk
                    )

                    self.assertEqual(len(list_zaken_req.qs), 2)
                    self.assertEqual(
                        list_zaken_req.qs,
                        {
                            "maximalevertrouwelijkheidaanduiding": [
                                VertrouwelijkheidsAanduidingen.beperkt_openbaar
                            ],
                            "rol__betrokkeneidentificatie__vestiging__vestigingsnummer": [
                                "1234"
                            ],
                        },
                    )

    def test_list_cases_for_eherkenning_user_missing_rsin(self, m):
        for mock in self.mocks:
            mock._setUpMocks(m)

        self.eherkenning_user.rsin = ""
        self.eherkenning_user.save()

        self.config.fetch_eherkenning_zaken_with_rsin = True
        self.config.save()

        m.reset_mock()

        self.client.force_login(user=self.eherkenning_user)
        response = self.client.get(self.inner_url, HTTP_HX_REQUEST="true")

        self.assertListEqual(response.context["cases"], [])
        for mock in self.mocks:
            # don't show internal cases
            self.assertNotContains(response, mock.zaak_intern["omschrijving"])
            self.assertNotContains(response, mock.zaak_intern["identificatie"])

        for zaken_root in ("zaken.nl", "andere-zaken.nl"):
            # check zaken request query parameters
            list_zaken_req = [
                req
                for req in m.request_history
                if req.hostname == zaken_root and req.path == "/api/v1/zaken"
            ]
            self.assertEqual(len(list_zaken_req), 0)

    def test_format_zaak_identificatie(self, m):
        for mock in self.mocks:
            mock._setUpMocks(m)

        config = OpenZaakConfig.get_solo()
        self.client.force_login(user=self.user)

        with self.subTest("formatting enabled"):
            config.reformat_esuite_zaak_identificatie = True
            config.save()

            response = self.client.get(self.inner_url, HTTP_HX_REQUEST="true")

            for mock in self.mocks:
                for e_suite_case in (
                    case
                    for case in response.context["cases"]
                    if case["uuid"] == mock.zaak2["uuid"]
                ):
                    self.assertEqual(e_suite_case["identification"], "6639-2022")

        with self.subTest("formatting disabled"):
            config.reformat_esuite_zaak_identificatie = False
            config.save()

            response = self.client.get(self.inner_url, HTTP_HX_REQUEST="true")

            for mock in self.mocks:
                for e_suite_case in (
                    case
                    for case in response.context["cases"]
                    if case["uuid"] == mock.zaak2["uuid"]
                ):
                    self.assertEqual(
                        e_suite_case["identification"], "0014ESUITE66392022"
                    )

    def test_reformat_esuite_zaak_identificatie(self, m):
        tests = [
            ("0014ESUITE66392022", "6639-2022"),
            ("4321ESUITE00011991", "0001-1991"),
            ("4321ESUITE123456781991", "12345678-1991"),
            ("12345678", "12345678"),
            ("aaaaaa1234", "aaaaaa1234"),
        ]

        for value, expected in tests:
            with self.subTest(value=value, expected=expected):
                actual = Zaak._reformat_esuite_zaak_identificatie(value)
                self.assertEqual(actual, expected)

    def test_list_cases_logs_displayed_case_ids(self, m):
        for mock in self.mocks:
            mock._setUpMocks(m)

        self.client.force_login(user=self.user)
        self.client.get(self.inner_url, HTTP_HX_REQUEST="true")

        # check access logs for displayed cases
        logs = list(TimelineLog.objects.all())

        case_log = [
            l
            for l in logs
            for mock in self.mocks
            if mock.zaak1["identificatie"] in l.extra_data["message"]
        ]
        self.assertEqual(len(case_log), 2)
        self.assertTrue(all(l.user == self.user for l in case_log))
        self.assertTrue(all(l.content_object == self.user for l in case_log))

        case_log = [
            l
            for l in logs
            for mock in self.mocks
            if mock.zaak2["identificatie"] in l.extra_data["message"]
        ]
        self.assertEqual(len(case_log), 2)
        self.assertTrue(all(l.user == self.user for l in case_log))
        self.assertTrue(all(l.content_object == self.user for l in case_log))

        # no logs for internal, hence non-displayed cases
        for log in logs:
            for mock in self.mocks:
                self.assertNotIn(
                    mock.zaak_intern["identificatie"], log.extra_data["message"]
                )

    @patch.object(InnerCaseListView, "paginate_by", 4)
    def test_list_cases_paginated(self, m):
        """
        show only cases from the first backend and url to the next page
        """
        for mock in self.mocks:
            mock._setUpMocks(m)

        # 1. test first page
        self.client.force_login(user=self.user)
        response_1 = self.client.get(self.inner_url, HTTP_HX_REQUEST="true")

        expected_cases = [
            [
                {
                    "uuid": mock.zaak2["uuid"],
                    "start_date": datetime.date.fromisoformat(mock.zaak2["startdatum"]),
                    "end_date": None,
                    "identification": mock.zaak2["identificatie"],
                    "description": mock.zaaktype["omschrijving"],
                    "current_status": mock.status_type_initial["omschrijving"],
                    "zaaktype_config": mock.zaaktype_config1,
                    "statustype_config": mock.zt_statustype_config1,
                    "case_type": "Zaak",
                    "api_group": self.api_groups[i],
                },
                {
                    "uuid": mock.zaak1["uuid"],
                    "start_date": datetime.date.fromisoformat(mock.zaak1["startdatum"]),
                    "end_date": None,
                    "identification": mock.zaak1["identificatie"],
                    "description": mock.zaaktype["omschrijving"],
                    "current_status": mock.status_type_initial["omschrijving"],
                    "zaaktype_config": mock.zaaktype_config1,
                    "statustype_config": mock.zt_statustype_config1,
                    "case_type": "Zaak",
                    "api_group": self.api_groups[i],
                },
                {
                    "uuid": mock.zaak3["uuid"],
                    "start_date": datetime.date.fromisoformat(mock.zaak3["startdatum"]),
                    "end_date": datetime.date.fromisoformat(mock.zaak3["einddatum"]),
                    "identification": mock.zaak3["identificatie"],
                    "description": mock.zaaktype["omschrijving"],
                    "current_status": mock.status_type_finish["statustekst"],
                    "zaaktype_config": mock.zaaktype_config1,
                    "statustype_config": None,
                    "case_type": "Zaak",
                    "api_group": self.api_groups[i],
                },
                {
                    "uuid": mock.zaak_result["uuid"],
                    "start_date": datetime.date.fromisoformat(
                        mock.zaak_result["startdatum"]
                    ),
                    "end_date": datetime.date(2022, 1, 13),
                    "identification": mock.zaak_result["identificatie"],
                    "description": mock.zaaktype["omschrijving"],
                    # use result here
                    "current_status": mock.resultaat_type["omschrijving"],
                    "zaaktype_config": mock.zaaktype_config1,
                    "statustype_config": mock.zt_statustype_config1,
                    "case_type": "Zaak",
                    "api_group": self.api_groups[i],
                },
            ]
            for i, mock in enumerate(self.mocks)
        ]

        self.assertListEqual(response_1.context.get("cases"), expected_cases[0])
        self.assertNotContains(response_1, self.mocks[0].zaak2["url"])
        self.assertContains(response_1, "?page=2")

        # 2. test page 2, where the responses from the second backend begin
        next_page = f"{self.inner_url}?page=2"
        response_2 = self.client.get(next_page, HTTP_HX_REQUEST="true")

        self.assertListEqual(response_2.context.get("cases"), expected_cases[1])
        self.assertNotContains(response_2, self.mocks[1].zaak2["url"])
        self.assertContains(response_2, "?page=1")

    @patch.object(InnerCaseListView, "paginate_by", 4)
    def test_list_cases_paginated_logs_displayed_case_ids(self, m):
        for mock in self.mocks:
            mock._setUpMocks(m)

        self.client.force_login(user=self.user)

        for page, mock in enumerate(self.mocks):
            with self.subTest(f"page {page + 1}"):
                url = self.inner_url + f"?page={page + 1}"
                response = self.client.get(url, HTTP_HX_REQUEST="true")

                expected_uuids = [
                    mock.zaak2["uuid"],
                    mock.zaak1["uuid"],
                    mock.zaak3["uuid"],
                    mock.zaak_result["uuid"],
                ]
                self.assertListEqual(
                    [c["uuid"] for c in response.context.get("cases")], expected_uuids
                )

                expected_identifications = [
                    mock.zaak2["identificatie"],
                    mock.zaak1["identificatie"],
                    mock.zaak3["identificatie"],
                    mock.zaak_result["identificatie"],
                ]
                self.assertTimelineLog(
                    f"Zaken bekeken: {', '.join(expected_identifications)}"
                )

                other_mock = self.mocks[0 if page == 1 else 1]
                with self.assertRaises(AssertionError):
                    self.assertTimelineLog(
                        message=other_mock.zaak1["identificatie"],
                        lookup=Lookups.icontains,
                    )
                    self.assertTimelineLog(
                        other_mock.zaak3["identificatie"], lookup=Lookups.icontains
                    )

                TimelineLog.objects.all().delete()


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class CaseSubmissionTest(TransactionWebTest):
    inner_url = reverse_lazy("cases:cases_content")

    def setUp(self):
        ZGWApiGroupConfigFactory(
            zrc_service__api_root=ZAKEN_ROOT,
            form_service__api_root=FORMS_ROOT,
        )
        ZGWApiGroupConfigFactory(
            zrc_service__api_root=ANOTHER_ZAKEN_ROOT,
            form_service__api_root=ANOTHER_FORMS_ROOT,
        )

    @requests_mock.Mocker()
    def test_get_open_submissions_by_bsn(self, m):
        digid_user = UserFactory(
            login_type=LoginTypeChoices.digid, bsn="900222086", email="john@smith.nl"
        )
        data = ESuiteSubmissionData(
            zaken_root=ZAKEN_ROOT, forms_root=FORMS_ROOT, user=digid_user
        ).install_digid_mocks(m)
        data_alt = ESuiteSubmissionData(
            zaken_root=ANOTHER_ZAKEN_ROOT,
            forms_root=ANOTHER_FORMS_ROOT,
            user=digid_user,
        ).install_digid_mocks(m)

        response = self.app.get(
            self.inner_url, user=digid_user, headers={"HX-Request": "true"}
        )

        cases = response.context["cases"]

        self.assertEqual(len(cases), 3)

        # submission cases are sorted in reverse by `last modified`
        self.assertEqual(cases[0]["url"], data_alt.submission_3["url"])
        self.assertEqual(cases[0]["uuid"], data_alt.submission_3["uuid"])
        self.assertEqual(cases[0]["naam"], data_alt.submission_3["naam"])
        self.assertEqual(cases[0]["vervolg_link"], data_alt.submission_3["vervolgLink"])
        self.assertEqual(
            cases[0]["datum_laatste_wijziging"].strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
            data_alt.submission_3["datumLaatsteWijziging"],
        )

        self.assertEqual(cases[1]["url"], data.submission_2["url"])
        self.assertEqual(cases[1]["uuid"], data.submission_2["uuid"])
        self.assertEqual(cases[1]["naam"], data.submission_2["naam"])
        self.assertEqual(cases[1]["vervolg_link"], data.submission_2["vervolgLink"])
        self.assertEqual(
            cases[1]["datum_laatste_wijziging"].strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
            data.submission_2["datumLaatsteWijziging"],
        )

    @requests_mock.Mocker()
    @patch("open_inwoner.kvk.middleware.kvk_branch_selected_done")
    def test_get_open_submissions_by_kvk(self, m, kvk_branch_selected):
        user = UserFactory(login_type=LoginTypeChoices.eherkenning, kvk="68750110")
        data = ESuiteSubmissionData(
            zaken_root=ZAKEN_ROOT, forms_root=FORMS_ROOT, user=user
        ).install_eherkenning_mocks(m)
        data_alt = ESuiteSubmissionData(
            zaken_root=ANOTHER_ZAKEN_ROOT, forms_root=ANOTHER_FORMS_ROOT, user=user
        ).install_eherkenning_mocks(m)

        response = self.app.get(
            self.inner_url, user=user, headers={"HX-Request": "true"}
        )

        cases = response.context["cases"]

        self.assertEqual(len(cases), 3)

        # submission cases are sorted in reverse by `last modified`
        self.assertEqual(cases[0]["url"], data_alt.submission_3["url"])
        self.assertEqual(cases[0]["uuid"], data_alt.submission_3["uuid"])
        self.assertEqual(cases[0]["naam"], data_alt.submission_3["naam"])
        self.assertEqual(cases[0]["vervolg_link"], data_alt.submission_3["vervolgLink"])
        self.assertEqual(
            cases[0]["datum_laatste_wijziging"].strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
            data_alt.submission_3["datumLaatsteWijziging"],
        )

        self.assertEqual(cases[1]["url"], data.submission_2["url"])
        self.assertEqual(cases[1]["uuid"], data.submission_2["uuid"])
        self.assertEqual(cases[1]["naam"], data.submission_2["naam"])
        self.assertEqual(cases[1]["vervolg_link"], data.submission_2["vervolgLink"])
        self.assertEqual(
            cases[1]["datum_laatste_wijziging"].strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
            data.submission_2["datumLaatsteWijziging"],
        )
