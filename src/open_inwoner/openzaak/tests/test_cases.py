import datetime
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.test import TransactionTestCase
from django.test.utils import override_settings
from django.urls import reverse_lazy

import requests_mock
from django_webtest import WebTest
from furl import furl
from timeline_logger.models import TimelineLog
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen
from zgw_consumers.constants import APITypes

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.tests.factories import UserFactory, eHerkenningUserFactory
from open_inwoner.cms.cases.views.cases import InnerCaseListView
from open_inwoner.openzaak.tests.shared import FORMS_ROOT
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
    ServiceFactory,
    StatusTranslationFactory,
    ZaakTypeConfigFactory,
    ZaakTypeStatusTypeConfigFactory,
)
from .helpers import generate_oas_component_cached
from .mocks import ESuiteData
from .shared import CATALOGI_ROOT, ZAKEN_ROOT

# Avoid redirects through `KvKLoginMiddleware`
PATCHED_MIDDLEWARE = [
    m
    for m in settings.MIDDLEWARE
    if m != "open_inwoner.kvk.middleware.KvKLoginMiddleware"
]


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class CaseListAccessTests(AssertRedirectsMixin, ClearCachesMixin, WebTest):
    outer_url = reverse_lazy("cases:index")
    inner_url = reverse_lazy("cases:cases_content")

    def setUp(self):
        super().setUp()

        # services
        self.zaak_service = ServiceFactory(api_root=ZAKEN_ROOT, api_type=APITypes.zrc)
        self.catalogi_service = ServiceFactory(
            api_root=CATALOGI_ROOT, api_type=APITypes.ztc
        )
        # openzaak config
        self.config = OpenZaakConfig.get_solo()
        self.config.zaak_service = self.zaak_service
        self.config.catalogi_service = self.catalogi_service
        self.config.save()

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

    def test_missing_zaak_client_returns_empty_list(self):
        user = UserFactory(
            login_type=LoginTypeChoices.digid, bsn="900222086", email="john@smith.nl"
        )
        self.config.zaak_service = None
        self.config.save()

        response = self.app.get(
            self.inner_url, user=user, headers={"HX-Request": "true"}
        )

        self.assertListEqual(response.context.get("cases"), [])

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
        # services
        self.zaak_service = ServiceFactory(api_root=ZAKEN_ROOT, api_type=APITypes.zrc)
        self.catalogi_service = ServiceFactory(
            api_root=CATALOGI_ROOT, api_type=APITypes.ztc
        )
        # openzaak config
        self.config = OpenZaakConfig.get_solo()
        self.config.zaak_service = self.zaak_service
        self.config.catalogi_service = self.catalogi_service
        self.config.zaak_max_confidentiality = (
            VertrouwelijkheidsAanduidingen.beperkt_openbaar
        )
        self.config.save()

        self.zaaktype = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            url=f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f",
            omschrijving="Coffee zaaktype",
            identificatie="ZAAK-2022-0000000001",
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            indicatieInternOfExtern="extern",
        )
        self.zaak_type_intern = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            url=f"{CATALOGI_ROOT}zaaktypen/53340e34-75a1-4b04-1234",
            omschrijving="Intern zaaktype",
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            indicatieInternOfExtern="intern",
        )
        self.status_type1 = generate_oas_component_cached(
            "ztc",
            "schemas/StatusType",
            url=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-777yu878km09",
            zaaktype=self.zaaktype["url"],
            omschrijving="Initial request",
            volgnummer=1,
            isEindstatus=False,
        )
        self.status_type2 = generate_oas_component_cached(
            "ztc",
            "schemas/StatusType",
            url=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-744516671fe4",
            zaaktype=self.zaaktype["url"],
            omschrijving="Finish",
            volgnummer=2,
            isEindstatus=True,
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
            statustype_url=self.status_type1["url"],
            status_indicator=StatusIndicators.warning,
            status_indicator_text="U moet documenten toevoegen",
            description="Lorem ipsum dolor sit amet",
            call_to_action_url="https://example.com",
            call_to_action_text="Click me",
        )
        # open
        self.zaak1 = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            uuid="d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            zaaktype=self.zaaktype["url"],
            identificatie="ZAAK-2022-0000000001",
            omschrijving="Coffee zaak 1",
            startdatum="2022-01-02",
            einddatum=None,
            status=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.status1 = generate_oas_component_cached(
            "zrc",
            "schemas/Status",
            url=self.zaak1["status"],
            zaak=self.zaak1["url"],
            statustype=self.status_type1["url"],
            datumStatusGezet="2021-01-12",
            statustoelichting="",
        )
        self.zaak2 = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/e4d469b9-6666-4bdd-bf42-b53445298102",
            uuid="e4d469b9-6666-4bdd-bf42-b53445298102",
            zaaktype=self.zaaktype["url"],
            identificatie="0014ESUITE66392022",
            omschrijving="Coffee zaak 2",
            startdatum="2022-01-12",
            einddatum=None,
            status=f"{ZAKEN_ROOT}statussen/3da81560-c7fc-476a-ad13-beu760sle929",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.status2 = generate_oas_component_cached(
            "zrc",
            "schemas/Status",
            url=self.zaak2["status"],
            zaak=self.zaak2["url"],
            statustype=self.status_type1["url"],
            datumStatusGezet="2021-03-12",
            statustoelichting="",
        )
        self.zaak_eherkenning1 = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/bf558d78-280d-4723-b8e8-2b6179cd74e3",
            uuid="bf558d78-280d-4723-b8e8-2b6179cd74e3",
            zaaktype=self.zaaktype["url"],
            identificatie="ZAAK-2022-0000000003",
            omschrijving="Coffee zaak 3",
            startdatum="2022-01-02",
            einddatum=None,
            status=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.zaak_eherkenning2 = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/ff5026c8-5d1f-4bd2-a069-58d4bf75ec8c",
            uuid="ff5026c8-5d1f-4bd2-a069-58d4bf75ec8c",
            zaaktype=self.zaaktype["url"],
            identificatie="ZAAK-2022-0000000004",
            omschrijving="Coffee zaak 4",
            startdatum="2022-02-02",
            einddatum=None,
            status=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        # closed
        self.zaak3 = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/6f8de38f-85ea-42d3-978c-845a033335a7",
            uuid="6f8de38f-85ea-42d3-978c-845a033335a7",
            zaaktype=self.zaaktype["url"],
            identificatie="ZAAK-2022-0001000003",
            omschrijving="Coffee zaak closed",
            startdatum="2021-07-26",
            einddatum="2022-01-16",
            status=f"{ZAKEN_ROOT}statussen/98659876-bbb3-476a-ad13-n3nvcght758js",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.status3 = generate_oas_component_cached(
            "zrc",
            "schemas/Status",
            url=self.zaak3["status"],
            zaak=self.zaak3["url"],
            statustype=self.status_type2["url"],
            datumStatusGezet="2021-03-15",
            statustoelichting="",
        )
        # not visible
        self.zaak_intern = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4ee0bf67d",
            uuid="d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            zaaktype=self.zaak_type_intern["url"],
            identificatie="ZAAK-2022-0000000009",
            omschrijving="Intern zaak",
            startdatum="2022-01-02",
            einddatum=None,
            status=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c90234500333",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.status_intern = generate_oas_component_cached(
            "zrc",
            "schemas/Status",
            url=self.zaak_intern["status"],
            zaak=self.zaak_intern["url"],
            statustype=self.status_type1["url"],
            datumStatusGezet="2021-01-12",
            statustoelichting="",
        )
        self.submission = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4ee0bf67d",
            uuid="c8yudeb7-490f-2cw9-h8wa-44h9830bf67d",
            naam="mysub",
            datum_laatste_wijziging="2023-10-10",
        )

    def _setUpMocks(self, m):
        m.get(
            furl(f"{ZAKEN_ROOT}zaken")
            .add(
                {
                    "rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn": self.user.bsn,
                    "maximaleVertrouwelijkheidaanduiding": VertrouwelijkheidsAanduidingen.beperkt_openbaar,
                }
            )
            .url,
            json=paginated_response(
                [self.zaak1, self.zaak2, self.zaak3, self.zaak_intern]
            ),
        )
        for identifier in [self.eherkenning_user.kvk, self.eherkenning_user.rsin]:
            m.get(
                furl(f"{ZAKEN_ROOT}zaken")
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
                furl(f"{ZAKEN_ROOT}zaken")
                .add(
                    {
                        "rol__betrokkeneIdentificatie__nietNatuurlijkPersoon__innNnpId": identifier,
                        "maximaleVertrouwelijkheidaanduiding": VertrouwelijkheidsAanduidingen.beperkt_openbaar,
                        "rol__betrokkeneIdentificatie__vestiging__vestigingsNummer": "1234",
                    }
                )
                .url,
                json=paginated_response([self.zaak_eherkenning1]),
            )
        for resource in [
            self.zaaktype,
            self.status_type1,
            self.status_type2,
            self.status1,
            self.status2,
            self.status3,
            self.zaak_intern,
            self.status_intern,
            self.zaak_type_intern,
        ]:
            m.get(resource["url"], json=resource)

    def test_list_cases(self, m):
        self._setUpMocks(m)

        # Added for https://taiga.maykinmedia.nl/project/open-inwoner/task/1904
        # In eSuite it is possible to reuse a StatusType for multiple ZaakTypen, which
        # led to errors when retrieving the ZaakTypeStatusTypeConfig. This duplicate
        # config is added to verify that that issue was solved
        ZaakTypeStatusTypeConfigFactory.create(
            statustype_url=self.status_type1["url"],
            status_indicator=StatusIndicators.warning,
            status_indicator_text="U moet documenten toevoegen",
            description="Lorem ipsum dolor sit amet",
            call_to_action_url="https://example.com",
            call_to_action_text="duplicate",
        )

        self.client.force_login(user=self.user)
        response = self.client.get(self.inner_url, HTTP_HX_REQUEST="true")

        self.assertListEqual(
            response.context["cases"],
            [
                {
                    "uuid": self.zaak2["uuid"],
                    "start_date": datetime.date.fromisoformat(self.zaak2["startdatum"]),
                    "end_date": None,
                    "identification": self.zaak2["identificatie"],
                    "description": self.zaaktype["omschrijving"],
                    "current_status": self.status_type1["omschrijving"],
                    "zaaktype_config": self.zaaktype_config1,
                    "statustype_config": self.zt_statustype_config1,
                    "case_type": "Zaak",
                },
                {
                    "uuid": self.zaak1["uuid"],
                    "start_date": datetime.date.fromisoformat(self.zaak1["startdatum"]),
                    "end_date": None,
                    "identification": self.zaak1["identificatie"],
                    "description": self.zaaktype["omschrijving"],
                    "current_status": self.status_type1["omschrijving"],
                    "zaaktype_config": self.zaaktype_config1,
                    "statustype_config": self.zt_statustype_config1,
                    "case_type": "Zaak",
                },
                {
                    "uuid": self.zaak3["uuid"],
                    "start_date": datetime.date.fromisoformat(self.zaak3["startdatum"]),
                    "end_date": datetime.date.fromisoformat(self.zaak3["einddatum"]),
                    "identification": self.zaak3["identificatie"],
                    "description": self.zaaktype["omschrijving"],
                    "current_status": self.status_type2["omschrijving"],
                    "zaaktype_config": self.zaaktype_config1,
                    "statustype_config": None,
                    "case_type": "Zaak",
                },
            ],
        )
        # don't show internal cases
        self.assertNotContains(response, self.zaak_intern["omschrijving"])
        self.assertNotContains(response, self.zaak_intern["identificatie"])

        # check zaken request query parameters
        list_zaken_req = [
            req
            for req in m.request_history
            if req.hostname == "zaken.nl" and req.path == "/api/v1/zaken"
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

    @set_kvk_branch_number_in_session(None)
    def test_list_cases_for_eherkenning_user(self, m):
        self._setUpMocks(m)

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

                self.assertListEqual(
                    response.context["cases"],
                    [
                        {
                            "uuid": self.zaak_eherkenning2["uuid"],
                            "start_date": datetime.date.fromisoformat(
                                self.zaak_eherkenning2["startdatum"]
                            ),
                            "end_date": None,
                            "identification": self.zaak_eherkenning2["identificatie"],
                            "description": self.zaaktype["omschrijving"],
                            "current_status": self.status_type1["omschrijving"],
                            "zaaktype_config": self.zaaktype_config1,
                            "statustype_config": self.zt_statustype_config1,
                            "case_type": "Zaak",
                        },
                        {
                            "uuid": self.zaak_eherkenning1["uuid"],
                            "start_date": datetime.date.fromisoformat(
                                self.zaak_eherkenning1["startdatum"]
                            ),
                            "end_date": None,
                            "identification": self.zaak_eherkenning1["identificatie"],
                            "description": self.zaaktype["omschrijving"],
                            "current_status": self.status_type1["omschrijving"],
                            "zaaktype_config": self.zaaktype_config1,
                            "statustype_config": self.zt_statustype_config1,
                            "case_type": "Zaak",
                        },
                    ],
                )
                # don't show internal cases
                self.assertNotContains(response, self.zaak_intern["omschrijving"])
                self.assertNotContains(response, self.zaak_intern["identificatie"])

                # check zaken request query parameters
                list_zaken_req = [
                    req
                    for req in m.request_history
                    if req.hostname == "zaken.nl" and req.path == "/api/v1/zaken"
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
        self._setUpMocks(m)
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

                self.assertListEqual(
                    response.context["cases"],
                    [
                        {
                            "uuid": self.zaak_eherkenning1["uuid"],
                            "start_date": datetime.date.fromisoformat(
                                self.zaak_eherkenning1["startdatum"]
                            ),
                            "end_date": None,
                            "identification": self.zaak_eherkenning1["identificatie"],
                            "description": self.zaaktype["omschrijving"],
                            "current_status": self.status_type1["omschrijving"],
                            "zaaktype_config": self.zaaktype_config1,
                            "statustype_config": self.zt_statustype_config1,
                            "case_type": "Zaak",
                        },
                    ],
                )
                # don't show internal cases
                self.assertNotContains(response, self.zaak_intern["omschrijving"])
                self.assertNotContains(response, self.zaak_intern["identificatie"])

                # check zaken request query parameters
                list_zaken_req = [
                    req
                    for req in m.request_history
                    if req.hostname == "zaken.nl" and req.path == "/api/v1/zaken"
                ][0]
                identifier = (
                    self.eherkenning_user.rsin
                    if fetch_eherkenning_zaken_with_rsin
                    else self.eherkenning_user.kvk
                )

                self.assertEqual(len(list_zaken_req.qs), 3)
                self.assertEqual(
                    list_zaken_req.qs,
                    {
                        "rol__betrokkeneidentificatie__nietnatuurlijkpersoon__innnnpid": [
                            identifier
                        ],
                        "maximalevertrouwelijkheidaanduiding": [
                            VertrouwelijkheidsAanduidingen.beperkt_openbaar
                        ],
                        "rol__betrokkeneidentificatie__vestiging__vestigingsnummer": [
                            "1234"
                        ],
                    },
                )

    def test_list_cases_for_eherkenning_user_missing_rsin(self, m):
        self._setUpMocks(m)

        self.eherkenning_user.rsin = ""
        self.eherkenning_user.save()

        self.config.fetch_eherkenning_zaken_with_rsin = True
        self.config.save()

        m.reset_mock()

        self.client.force_login(user=self.eherkenning_user)
        response = self.client.get(self.inner_url, HTTP_HX_REQUEST="true")

        self.assertListEqual(response.context["cases"], [])
        # don't show internal cases
        self.assertNotContains(response, self.zaak_intern["omschrijving"])
        self.assertNotContains(response, self.zaak_intern["identificatie"])

        # check zaken request query parameters
        list_zaken_req = [
            req
            for req in m.request_history
            if req.hostname == "zaken.nl" and req.path == "/api/v1/zaken"
        ]
        self.assertEqual(len(list_zaken_req), 0)

    def test_format_zaak_identificatie(self, m):
        config = OpenZaakConfig.get_solo()
        self._setUpMocks(m)
        self.client.force_login(user=self.user)

        with self.subTest("formatting enabled"):
            config.reformat_esuite_zaak_identificatie = True
            config.save()

            response = self.client.get(self.inner_url, HTTP_HX_REQUEST="true")

            e_suite_case = next(
                (
                    case
                    for case in response.context["cases"]
                    if case["uuid"] == self.zaak2["uuid"]
                )
            )

            self.assertEqual(e_suite_case["identification"], "6639-2022")

        with self.subTest("formatting disabled"):
            config.reformat_esuite_zaak_identificatie = False
            config.save()

            response = self.client.get(self.inner_url, HTTP_HX_REQUEST="true")

            e_suite_case = next(
                (
                    case
                    for case in response.context["cases"]
                    if case["uuid"] == self.zaak2["uuid"]
                )
            )

            self.assertEqual(e_suite_case["identification"], "0014ESUITE66392022")

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

    def test_list_cases_translates_status(self, m):
        st1 = StatusTranslationFactory(
            status=self.status_type1["omschrijving"],
            translation="Translated Status Type",
        )
        self._setUpMocks(m)
        self.client.force_login(user=self.user)
        response = self.client.get(self.inner_url, HTTP_HX_REQUEST="true")

        self.assertNotContains(response, st1.status)
        self.assertContains(response, st1.translation)

    def test_list_cases_logs_displayed_case_ids(self, m):
        self._setUpMocks(m)

        self.client.force_login(user=self.user)
        self.client.get(self.inner_url, HTTP_HX_REQUEST="true")

        # check access logs for displayed cases
        logs = list(TimelineLog.objects.all())

        case_log = [
            l for l in logs if self.zaak1["identificatie"] in l.extra_data["message"]
        ]
        self.assertEqual(len(case_log), 1)
        self.assertEqual(self.user, case_log[0].user)
        self.assertEqual(self.user, case_log[0].content_object)

        case_log = [
            l for l in logs if self.zaak2["identificatie"] in l.extra_data["message"]
        ]
        self.assertEqual(len(case_log), 1)
        self.assertEqual(self.user, case_log[0].user)
        self.assertEqual(self.user, case_log[0].content_object)

        # no logs for internal, hence non-displayed cases
        for log in logs:
            self.assertNotIn(
                self.zaak_intern["identificatie"], log.extra_data["message"]
            )

    @patch.object(InnerCaseListView, "paginate_by", 1)
    def test_list_cases_paginated(self, m):
        """
        show only one case and url to the next page
        """
        self._setUpMocks(m)

        # 1. test first page
        self.client.force_login(user=self.user)
        response_1 = self.client.get(self.inner_url, HTTP_HX_REQUEST="true")

        self.assertListEqual(
            response_1.context.get("cases"),
            [
                {
                    "uuid": self.zaak2["uuid"],
                    "start_date": datetime.date.fromisoformat(self.zaak2["startdatum"]),
                    "end_date": None,
                    "identification": self.zaak2["identificatie"],
                    "description": self.zaaktype["omschrijving"],
                    "current_status": self.status_type1["omschrijving"],
                    "zaaktype_config": self.zaaktype_config1,
                    "statustype_config": self.zt_statustype_config1,
                    "case_type": "Zaak",
                },
            ],
        )
        self.assertNotContains(response_1, self.zaak1["identificatie"])
        self.assertContains(response_1, "?page=2")

        # 2. test next page
        next_page = f"{self.inner_url}?page=2"
        response_2 = self.client.get(next_page, HTTP_HX_REQUEST="true")

        self.assertListEqual(
            response_2.context.get("cases"),
            [
                {
                    "uuid": self.zaak1["uuid"],
                    "start_date": datetime.date.fromisoformat(self.zaak1["startdatum"]),
                    "end_date": None,
                    "identification": self.zaak1["identificatie"],
                    "description": self.zaaktype["omschrijving"],
                    "current_status": self.status_type1["omschrijving"],
                    "zaaktype_config": self.zaaktype_config1,
                    "statustype_config": self.zt_statustype_config1,
                    "case_type": "Zaak",
                },
            ],
        )
        self.assertNotContains(response_2, self.zaak2["identificatie"])
        self.assertContains(response_2, "?page=1")

    @patch.object(InnerCaseListView, "paginate_by", 1)
    def test_list_cases_paginated_logs_displayed_case_ids(self, m):
        self._setUpMocks(m)
        self.client.force_login(user=self.user)

        with self.subTest("first page"):
            response = self.client.get(self.inner_url, HTTP_HX_REQUEST="true")
            self.assertEqual(
                response.context.get("cases")[0]["uuid"], self.zaak2["uuid"]
            )

            self.assertTimelineLog(f"Zaken bekeken: {self.zaak2['identificatie']}")

            with self.assertRaises(AssertionError):
                self.assertTimelineLog(
                    self.zaak1["identificatie"], lookup=Lookups.icontains
                )
                self.assertTimelineLog(
                    self.zaak3["identificatie"], lookup=Lookups.icontains
                )

        TimelineLog.objects.all().delete()

        with self.subTest("next page"):
            next_page = f"{self.inner_url}?page=2"
            response = self.client.get(next_page, HTTP_HX_REQUEST="true")
            self.assertEqual(
                response.context.get("cases")[0]["uuid"], self.zaak1["uuid"]
            )

            self.assertTimelineLog(f"Zaken bekeken: {self.zaak1['identificatie']}")

            with self.assertRaises(AssertionError):
                self.assertTimelineLog(
                    self.zaak2["identificatie"], lookup=Lookups.icontains
                )
                self.assertTimelineLog(
                    self.zaak3["identificatie"], lookup=Lookups.icontains
                )


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class CaseSubmissionTest(WebTest):
    inner_url = reverse_lazy("cases:cases_content")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.config = OpenZaakConfig.get_solo()
        cls.config.form_service = ServiceFactory(
            api_root=FORMS_ROOT, api_type=APITypes.orc
        )
        cls.config.save()

    @requests_mock.Mocker()
    def test_case_submission(self, m):
        user = UserFactory(
            login_type=LoginTypeChoices.digid, bsn="900222086", email="john@smith.nl"
        )

        data = ESuiteData().install_mocks(m)

        response = self.app.get(
            self.inner_url, user=user, headers={"HX-Request": "true"}
        )

        cases = response.context["cases"]

        self.assertEqual(len(cases), 2)

        # submission cases are sorted in reverse by `last modified`
        self.assertEqual(cases[0]["url"], data.submission_2["url"])
        self.assertEqual(cases[0]["uuid"], data.submission_2["uuid"])
        self.assertEqual(cases[0]["naam"], data.submission_2["naam"])
        self.assertEqual(cases[0]["vervolg_link"], data.submission_2["vervolgLink"])
        self.assertEqual(
            cases[0]["datum_laatste_wijziging"].strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
            data.submission_2["datumLaatsteWijziging"],
        )
