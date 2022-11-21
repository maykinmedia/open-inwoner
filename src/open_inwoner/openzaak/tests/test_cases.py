import datetime

from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.urls import reverse

import requests_mock
from django_webtest import WebTest
from freezegun import freeze_time
from furl import furl
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen
from zgw_consumers.constants import APITypes
from zgw_consumers.test import generate_oas_component, mock_service_oas_get

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.openzaak.cases import fetch_single_case
from open_inwoner.utils.test import paginated_response

from ..models import OpenZaakConfig
from .factories import ServiceFactory

ZAKEN_ROOT = "https://zaken.nl/api/v1/"
CATALOGI_ROOT = "https://catalogi.nl/api/v1/"


@requests_mock.Mocker()
class TestListCasesView(WebTest):
    def setUp(self):
        self.maxDiff = None

    @classmethod
    def setUpTestData(self):
        super().setUpTestData()

        self.user = UserFactory(
            login_type=LoginTypeChoices.digid, bsn="900222086", email="johm@smith.nl"
        )
        # services
        self.zaak_service = ServiceFactory(api_root=ZAKEN_ROOT, api_type=APITypes.zrc)
        self.catalogi_service = ServiceFactory(
            api_root=CATALOGI_ROOT, api_type=APITypes.ztc
        )
        # operzaak config
        self.config = OpenZaakConfig.get_solo()
        self.config.zaak_service = self.zaak_service
        self.config.catalogi_service = self.catalogi_service
        self.config.zaak_max_confidentiality = (
            VertrouwelijkheidsAanduidingen.beperkt_openbaar
        )
        self.config.save()

        self.zaak1 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f",
            identificatie="ZAAK-2022-0000000024",
            omschrijving="Zaak naar aanleiding van ingezonden formulier",
            startdatum="2022-01-02",
            einddatum="2022-01-16",
            status=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.zaak2 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/e4d469b9-6666-4bdd-bf42-b53445298102",
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f",
            identificatie="ZAAK-2022-0008800024",
            omschrijving="Zaak naar aanleiding van ingezonden formulier",
            startdatum="2022-01-12",
            einddatum=None,
            status=f"{ZAKEN_ROOT}statussen/3da81560-c7fc-476a-ad13-beu760sle929",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.zaak3 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/6f8de38f-85ea-42d3-978c-845a033335a7",
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f",
            identificatie="ZAAK-2022-0001000024",
            omschrijving="Zaak naar aanleiding van ingezonden formulier",
            startdatum="2021-07-26",
            einddatum=None,
            status=f"{ZAKEN_ROOT}statussen/98659876-bbb3-476a-ad13-n3nvcght758js",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.zaaktype = generate_oas_component(
            "ztc",
            "schemas/ZaakType",
            url=f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f",
            omschrijving="Coffee zaaktype",
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            vertrouwelijkheidaanduiding="openbaar",
            doel="Ask for coffee",
            aanleiding="Coffee is essential",
            indicatie_intern_of_extern="intern",
            handeling_initiator="Request",
            onderwerp="Coffee",
            handeling_behandelaar="Behandelen",
            opschorting_en_aanhouding_mogelijk=False,
            verlenging_mogelijk=False,
            publicatie_indicatie=False,
            besluittypen=[],
            begin_geldigheid="2020-09-25",
            versiedatum="2020-09-25",
        )
        self.status1 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}statussen/3da81560-c7fc-476a-ad13-beu760sle929",
            zaak=f"{ZAKEN_ROOT}zaken/e4d469b9-6666-4bdd-bf42-b53445298102",
            statustype=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-777yu878km09",
            datum_status_gezet="2021-01-12",
            statustoelichting="",
        )
        self.status2 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
            zaak=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            statustype=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-744516671fe4",
            datum_status_gezet="2021-03-12",
            statustoelichting="",
        )
        self.status3 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}statussen/98659876-bbb3-476a-ad13-n3nvcght758js",
            zaak=f"{ZAKEN_ROOT}zaken/6f8de38f-85ea-42d3-978c-845a033335a7",
            statustype=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-744516671fe4",
            datum_status_gezet="2021-03-15",
            statustoelichting="",
        )
        self.status_type1 = generate_oas_component(
            "ztc",
            "schemas/StatusType",
            url=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-777yu878km09",
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f-8ff7e6a73c2c",
            omschrijving="Initial request",
            omschrijving_generiek="",
            statustekst="",
            volgnummer=1,
            is_eindstatus=False,
        )
        self.status_type2 = generate_oas_component(
            "ztc",
            "schemas/StatusType",
            url=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-744516671fe4",
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f-8ff7e6a73c2c",
            omschrijving="Finish",
            omschrijving_generiek="",
            statustekst="",
            volgnummer=1,
            is_eindstatus=False,
        )

    def tearDown(self):
        cache.clear()

    def _setUpMocks(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        m.get(
            furl(f"{ZAKEN_ROOT}zaken")
            .add(
                {
                    "rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn": self.user.bsn,
                    "maximaleVertrouwelijkheidaanduiding": VertrouwelijkheidsAanduidingen.beperkt_openbaar,
                }
            )
            .url,
            json=paginated_response([self.zaak1, self.zaak2, self.zaak3]),
        )
        m.get(f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f", json=self.zaaktype)
        m.get(
            f"{CATALOGI_ROOT}statustypen",
            json=paginated_response([self.status_type1, self.status_type2]),
        )
        m.get(
            f"{ZAKEN_ROOT}statussen/3da81560-c7fc-476a-ad13-beu760sle929",
            json=self.status1,
        )
        m.get(
            f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
            json=self.status2,
        )
        m.get(
            f"{ZAKEN_ROOT}statussen/98659876-bbb3-476a-ad13-n3nvcght758js",
            json=self.status3,
        )
        m.get(
            f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-777yu878km09",
            json=self.status_type1,
        )
        m.get(
            f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-744516671fe4",
            json=self.status_type2,
        )

    def test_sorted_cases_are_retrieved_when_user_logged_in_via_digid(self, m):
        self._setUpMocks(m)

        response = self.app.get(reverse("accounts:my_cases"), user=self.user)
        self.assertListEqual(
            response.context.get("open_cases"),
            [
                {
                    "uuid": "6f8de38f-85ea-42d3-978c-845a033335a7",
                    "start_date": datetime.date(2021, 7, 26),
                    "end_date": None,
                    "description": "Zaak naar aanleiding van ingezonden formulier",
                    "zaaktype_description": "Coffee zaaktype",
                    "current_status": "Finish",
                },
                {
                    "uuid": "e4d469b9-6666-4bdd-bf42-b53445298102",
                    "start_date": datetime.date(2022, 1, 12),
                    "end_date": None,
                    "description": "Zaak naar aanleiding van ingezonden formulier",
                    "zaaktype_description": "Coffee zaaktype",
                    "current_status": "Initial request",
                },
            ],
        )
        self.assertListEqual(
            response.context.get("closed_cases"),
            [
                {
                    "uuid": "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
                    "start_date": datetime.date(2022, 1, 2),
                    "end_date": datetime.date(2022, 1, 16),
                    "description": "Zaak naar aanleiding van ingezonden formulier",
                    "zaaktype_description": "Coffee zaaktype",
                    "current_status": "Finish",
                }
            ],
        )
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

    def test_case_types_are_cached(self, m):
        self._setUpMocks(m)

        # Cache is empty before the request
        self.assertIsNone(cache.get(f"case_type:{self.zaaktype['url']}"))

        self.app.get(reverse("accounts:my_cases"), user=self.user)

        # Case type is cached after the request
        self.assertIsNotNone(cache.get(f"case_type:{self.zaaktype['url']}"))

    def test_cached_case_types_are_deleted_after_one_day(self, m):
        self._setUpMocks(m)

        with freeze_time("2022-01-01 12:00") as frozen_time:
            self.app.get(reverse("accounts:my_cases"), user=self.user)

            # After one day the results should be deleted
            frozen_time.tick(delta=datetime.timedelta(days=1))
            self.assertIsNone(cache.get(f"case_type:{self.zaaktype['url']}"))

    def test_cached_case_types_in_combination_with_new_ones(self, m):
        self._setUpMocks(m)

        # First attempt
        self.assertIsNone(cache.get(f"case_type:{self.zaaktype['url']}"))

        self.app.get(reverse("accounts:my_cases"), user=self.user)

        self.assertIsNotNone(cache.get(f"case_type:{self.zaaktype['url']}"))

        # Second attempt with new case and case type
        new_zaak = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/a25b2dce-1cae-4fc9-b9e9-141b0ad5189f",
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f-98ui7y87i876",
            identificatie="ZAAK-2022-0000000024",
            omschrijving="Zaak naar aanleiding van ingezonden formulier",
            startdatum="2022-01-02",
            einddatum=None,
            status=f"{ZAKEN_ROOT}statussen/3da81560-c7fc-476a-ad13-oie8u899923g",
        )
        new_zaaktype = generate_oas_component(
            "ztc",
            "schemas/ZaakType",
            url=f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f-98ui7y87i876",
            omschrijving="Coffee zaaktype",
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            vertrouwelijkheidaanduiding="openbaar",
            doel="Ask for coffee",
            aanleiding="Coffee is essential",
            indicatie_intern_of_extern="intern",
            handeling_initiator="Request",
            onderwerp="Coffee",
            handeling_behandelaar="Behandelen",
            opschorting_en_aanhouding_mogelijk=False,
            verlenging_mogelijk=False,
            publicatie_indicatie=False,
            besluittypen=[],
            begin_geldigheid="2020-09-25",
            versiedatum="2020-09-25",
        )
        new_status = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}statussen/3da81560-c7fc-476a-ad13-oie8u899923g",
            zaak=f"{ZAKEN_ROOT}zaken/a25b2dce-1cae-4fc9-b9e9-141b0ad5189f",
            statustype=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-984yr8887rhe",
            datum_status_gezet="2021-01-12",
            statustoelichting="",
        )
        new_status_type = generate_oas_component(
            "ztc",
            "schemas/StatusType",
            url=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-984yr8887rhe",
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f-98ui7y87i876",
            omschrijving="Finish",
            omschrijving_generiek="",
            statustekst="",
            volgnummer=1,
            is_eindstatus=False,
        )
        m.get(
            f"{ZAKEN_ROOT}zaken?rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn=900222086",
            json=paginated_response([self.zaak1, self.zaak2, self.zaak3, new_zaak]),
        )
        m.get(
            f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f-98ui7y87i876",
            json=new_zaaktype,
        )
        m.get(
            f"{CATALOGI_ROOT}statustypen",
            json=paginated_response(
                [self.status_type1, self.status_type2, new_status_type]
            ),
        )
        m.get(
            f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-984yr8887rhe",
            json=new_status_type,
        )
        m.get(
            f"{ZAKEN_ROOT}statussen/3da81560-c7fc-476a-ad13-oie8u899923g",
            json=new_status,
        )

        self.assertIsNone(cache.get(f"case_type:{new_zaaktype['url']}"))

        self.app.get(reverse("accounts:my_cases"), user=self.user)

        self.assertIsNotNone(cache.get(f"case_type:{self.zaaktype['url']}"))
        self.assertIsNotNone(cache.get(f"case_type:{new_zaaktype['url']}"))

    def test_status_types_are_cached(self, m):
        self._setUpMocks(m)

        # Cache is empty before the request
        self.assertIsNone(
            cache.get(f"status_types_for_case_type:{self.zaaktype['url']}")
        )
        self.assertIsNone(
            cache.get(f"status_types_for_case_type:{self.zaaktype['url']}")
        )

        self.app.get(reverse("accounts:my_cases"), user=self.user)

        # Case type is cached after the request
        self.assertIsNotNone(
            cache.get(f"status_types_for_case_type:{self.zaaktype['url']}")
        )
        self.assertIsNotNone(
            cache.get(f"status_types_for_case_type:{self.zaaktype['url']}")
        )

    def test_cached_status_types_are_deleted_after_one_day(self, m):
        self._setUpMocks(m)

        with freeze_time("2022-01-01 12:00") as frozen_time:
            self.app.get(reverse("accounts:my_cases"), user=self.user)

            # After one day the results should be deleted
            frozen_time.tick(delta=datetime.timedelta(hours=24))
            self.assertIsNone(
                cache.get(f"status_types_for_case_type:{self.zaaktype['url']}")
            )
            self.assertIsNone(
                cache.get(f"status_types_for_case_type:{self.zaaktype['url']}")
            )

    def test_cached_status_types_in_combination_with_new_ones(self, m):
        self._setUpMocks(m)

        # First attempt
        self.assertIsNone(
            cache.get(f"status_types_for_case_type:{self.zaaktype['url']}")
        )
        self.assertIsNone(
            cache.get(f"status_types_for_case_type:{self.zaaktype['url']}")
        )

        self.app.get(reverse("accounts:my_cases"), user=self.user)

        self.assertIsNotNone(
            cache.get(f"status_types_for_case_type:{self.zaaktype['url']}")
        )
        self.assertIsNotNone(
            cache.get(f"status_types_for_case_type:{self.zaaktype['url']}")
        )

        # Second attempt with new case and status type
        new_zaak = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/a25b2dce-1cae-4fc9-b9e9-141b0ad5189f",
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f-98ui7y87i876",
            identificatie="ZAAK-2022-0000000024",
            omschrijving="Zaak naar aanleiding van ingezonden formulier",
            startdatum="2022-01-02",
            einddatum=None,
            status=f"{ZAKEN_ROOT}statussen/3da81560-c7fc-476a-ad13-oie8u899923g",
        )
        new_zaaktype = generate_oas_component(
            "ztc",
            "schemas/ZaakType",
            url=f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f-98ui7y87i876",
            omschrijving="Coffee zaaktype",
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            vertrouwelijkheidaanduiding="openbaar",
            doel="Ask for coffee",
            aanleiding="Coffee is essential",
            indicatie_intern_of_extern="intern",
            handeling_initiator="Request",
            onderwerp="Coffee",
            handeling_behandelaar="Behandelen",
            opschorting_en_aanhouding_mogelijk=False,
            verlenging_mogelijk=False,
            publicatie_indicatie=False,
            besluittypen=[],
            begin_geldigheid="2020-09-25",
            versiedatum="2020-09-25",
        )
        new_status = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}statussen/3da81560-c7fc-476a-ad13-oie8u899923g",
            zaak=f"{ZAKEN_ROOT}zaken/a25b2dce-1cae-4fc9-b9e9-141b0ad5189f",
            statustype=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-984yr8887rhe",
            datum_status_gezet="2021-01-12",
            statustoelichting="",
        )
        new_status_type = generate_oas_component(
            "ztc",
            "schemas/StatusType",
            url=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-984yr8887rhe",
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f-98ui7y87i876",
            omschrijving="Finish",
            omschrijving_generiek="",
            statustekst="",
            volgnummer=1,
            is_eindstatus=False,
        )
        m.get(
            f"{ZAKEN_ROOT}zaken?rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn=900222086",
            json=paginated_response([self.zaak1, self.zaak2, self.zaak3, new_zaak]),
        )
        m.get(
            f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f-98ui7y87i876",
            json=new_zaaktype,
        )
        m.get(
            f"{CATALOGI_ROOT}statustypen",
            json=paginated_response(
                [self.status_type1, self.status_type2, new_status_type]
            ),
        )
        m.get(
            f"{ZAKEN_ROOT}statussen/3da81560-c7fc-476a-ad13-oie8u899923g",
            json=new_status,
        )

        self.assertIsNone(
            cache.get(f"status_types_for_case_type:{new_zaaktype['url']}")
        )

        self.app.get(reverse("accounts:my_cases"), user=self.user)

        self.assertIsNotNone(
            cache.get(f"status_types_for_case_type:{new_zaaktype['url']}")
        )
        self.assertIsNotNone(
            cache.get(f"status_types_for_case_type:{self.zaaktype['url']}")
        )
        self.assertIsNotNone(
            cache.get(f"status_types_for_case_type:{self.zaaktype['url']}")
        )

    def test_statuses_are_cached(self, m):
        self._setUpMocks(m)

        # Cache is empty before the request
        self.assertIsNone(cache.get(f"status:{self.status1['url']}"))
        self.assertIsNone(cache.get(f"status:{self.status2['url']}"))
        self.assertIsNone(cache.get(f"status:{self.status3['url']}"))

        self.app.get(reverse("accounts:my_cases"), user=self.user)

        # Status is cached after the request
        self.assertIsNotNone(cache.get(f"status:{self.status1['url']}"))
        self.assertIsNotNone(cache.get(f"status:{self.status2['url']}"))
        self.assertIsNotNone(cache.get(f"status:{self.status3['url']}"))

    def test_cached_statuses_are_deleted_after_one_hour(self, m):
        self._setUpMocks(m)

        with freeze_time("2022-01-01 12:00") as frozen_time:
            self.app.get(reverse("accounts:my_cases"), user=self.user)

            # After one hour the results should be deleted
            frozen_time.tick(delta=datetime.timedelta(hours=1))
            self.assertIsNone(cache.get(f"status:{self.status1['url']}"))
            self.assertIsNone(cache.get(f"status:{self.status2['url']}"))
            self.assertIsNone(cache.get(f"status:{self.status3['url']}"))

    def test_cached_statuses_in_combination_with_new_ones(self, m):
        self._setUpMocks(m)

        # First attempt
        self.assertIsNone(cache.get(f"status:{self.status1['url']}"))
        self.assertIsNone(cache.get(f"status:{self.status2['url']}"))
        self.assertIsNone(cache.get(f"status:{self.status3['url']}"))

        self.app.get(reverse("accounts:my_cases"), user=self.user)

        self.assertIsNotNone(cache.get(f"status:{self.status1['url']}"))
        self.assertIsNotNone(cache.get(f"status:{self.status2['url']}"))
        self.assertIsNotNone(cache.get(f"status:{self.status3['url']}"))

        # Second attempt with new case and status type
        new_zaak = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/a25b2dce-1cae-4fc9-b9e9-141b0ad5189f",
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f-98ui7y87i876",
            identificatie="ZAAK-2022-0000000024",
            omschrijving="Zaak naar aanleiding van ingezonden formulier",
            startdatum="2022-01-02",
            einddatum=None,
            status=f"{ZAKEN_ROOT}statussen/3da81560-c7fc-476a-ad13-oie8u899923g",
        )
        new_zaaktype = generate_oas_component(
            "ztc",
            "schemas/ZaakType",
            url=f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f-98ui7y87i876",
            omschrijving="Coffee zaaktype",
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            vertrouwelijkheidaanduiding="openbaar",
            doel="Ask for coffee",
            aanleiding="Coffee is essential",
            indicatie_intern_of_extern="intern",
            handeling_initiator="Request",
            onderwerp="Coffee",
            handeling_behandelaar="Behandelen",
            opschorting_en_aanhouding_mogelijk=False,
            verlenging_mogelijk=False,
            publicatie_indicatie=False,
            besluittypen=[],
            begin_geldigheid="2020-09-25",
            versiedatum="2020-09-25",
        )
        new_status = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}statussen/3da81560-c7fc-476a-ad13-oie8u899923g",
            zaak=f"{ZAKEN_ROOT}zaken/a25b2dce-1cae-4fc9-b9e9-141b0ad5189f",
            statustype=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-984yr8887rhe",
            datum_status_gezet="2021-01-12",
            statustoelichting="",
        )
        new_status_type = generate_oas_component(
            "ztc",
            "schemas/StatusType",
            url=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-984yr8887rhe",
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f-98ui7y87i876",
            omschrijving="Finish",
            omschrijving_generiek="",
            statustekst="",
            volgnummer=1,
            is_eindstatus=False,
        )
        m.get(
            f"{ZAKEN_ROOT}zaken?rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn=900222086",
            json=paginated_response([self.zaak1, self.zaak2, self.zaak3, new_zaak]),
        )
        m.get(
            f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f-98ui7y87i876",
            json=new_zaaktype,
        )
        m.get(
            f"{CATALOGI_ROOT}statustypen",
            json=paginated_response(
                [self.status_type1, self.status_type2, new_status_type]
            ),
        )
        m.get(
            f"{ZAKEN_ROOT}statussen/3da81560-c7fc-476a-ad13-oie8u899923g",
            json=new_status,
        )
        m.get(
            f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-984yr8887rhe",
            json=new_status_type,
        )

        self.assertIsNone(cache.get(f"status:{new_status['url']}"))

        self.app.get(reverse("accounts:my_cases"), user=self.user)

        self.assertIsNotNone(cache.get(f"status:{new_status['url']}"))
        self.assertIsNotNone(cache.get(f"status:{self.status1['url']}"))
        self.assertIsNotNone(cache.get(f"status:{self.status2['url']}"))
        self.assertIsNotNone(cache.get(f"status:{self.status3['url']}"))

    def test_status_type_is_manually_retrieved_if_not_in_status_types(self, m):
        self._setUpMocks(m)
        m.get(
            f"{CATALOGI_ROOT}statustypen",
            json=paginated_response([self.status_type1]),
        )

        response = self.app.get(reverse("accounts:my_cases"), user=self.user)
        self.assertListEqual(
            response.context.get("open_cases"),
            [
                {
                    "uuid": "6f8de38f-85ea-42d3-978c-845a033335a7",
                    "start_date": datetime.date(2021, 7, 26),
                    "end_date": None,
                    "description": "Zaak naar aanleiding van ingezonden formulier",
                    "zaaktype_description": "Coffee zaaktype",
                    "current_status": "Finish",
                },
                {
                    "uuid": "e4d469b9-6666-4bdd-bf42-b53445298102",
                    "start_date": datetime.date(2022, 1, 12),
                    "end_date": None,
                    "description": "Zaak naar aanleiding van ingezonden formulier",
                    "zaaktype_description": "Coffee zaaktype",
                    "current_status": "Initial request",
                },
            ],
        )
        self.assertListEqual(
            response.context.get("closed_cases"),
            [
                {
                    "uuid": "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
                    "start_date": datetime.date(2022, 1, 2),
                    "end_date": datetime.date(2022, 1, 16),
                    "description": "Zaak naar aanleiding van ingezonden formulier",
                    "zaaktype_description": "Coffee zaaktype",
                    "current_status": "Finish",
                }
            ],
        )

    def test_user_is_redirected_to_root_when_not_logged_in_via_digid(self, m):
        self._setUpMocks(m)

        # User's bsn is None when logged in by email (default method)
        user = UserFactory(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.default,
        )
        response = self.app.get(reverse("accounts:my_cases"), user=user)

        self.assertRedirects(response, reverse("root"))

    def test_anonymous_user_has_no_access_to_cases_page(self, m):
        user = AnonymousUser()
        response = self.app.get(reverse("accounts:my_cases"), user=user)

        self.assertRedirects(
            response, f"{reverse('login')}?next={reverse('accounts:my_cases')}"
        )

    def test_missing_zaak_client_returns_empty_list(self, m):
        self._setUpMocks(m)

        self.config.zaak_service = None
        self.config.save()

        response = self.app.get(reverse("accounts:my_cases"), user=self.user)

        self.assertEquals(response.status_code, 200)
        self.assertListEqual(response.context.get("open_cases"), [])
        self.assertListEqual(response.context.get("closed_cases"), [])

    def test_no_cases_are_retrieved_when_http_404(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        m.get(
            f"{ZAKEN_ROOT}zaken?rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn=900222086",
            status_code=404,
        )
        m.get(f"{CATALOGI_ROOT}zaaktypen", json=paginated_response([self.zaaktype]))
        m.get(
            f"{CATALOGI_ROOT}statustypen",
            json=paginated_response([self.status_type1]),
        )

        response = self.app.get(reverse("accounts:my_cases"), user=self.user)

        self.assertEquals(response.status_code, 200)
        self.assertListEqual(response.context.get("open_cases"), [])
        self.assertListEqual(response.context.get("closed_cases"), [])

    def test_no_cases_are_retrieved_when_http_500(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        m.get(
            f"{ZAKEN_ROOT}zaken?rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn=900222086",
            status_code=500,
        )
        m.get(f"{CATALOGI_ROOT}zaaktypen", json=paginated_response([self.zaaktype]))
        m.get(
            f"{CATALOGI_ROOT}statustypen",
            json=paginated_response([self.status_type1]),
        )

        response = self.app.get(reverse("accounts:my_cases"), user=self.user)

        self.assertEquals(response.status_code, 200)
        self.assertListEqual(response.context.get("open_cases"), [])
        self.assertListEqual(response.context.get("closed_cases"), [])


@requests_mock.Mocker()
class TestFetchSpecificCase(WebTest):
    def setUp(self):
        self.config = OpenZaakConfig.get_solo()
        self.zaak_service = ServiceFactory(api_root=ZAKEN_ROOT, api_type=APITypes.zrc)
        self.config.zaak_service = self.zaak_service
        self.config.save()

        self.zaak = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            identificatie="ZAAK-2022-0000000024",
            omschrijving="Zaak naar aanleiding van ingezonden formulier",
            startdatum="2022-01-02",
            einddatum=None,
        )

    def _setUpMocks(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        m.get(
            f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            json=self.zaak,
        )

    def test_case_is_retrieved(self, m):
        self._setUpMocks(m)

        case = fetch_single_case("d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d")

        self.assertEquals(
            case.url,
            f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
        )

    def test_no_case_is_retrieved_when_http_404(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        m.get(
            f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            status_code=404,
        )

        case = fetch_single_case("d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d")

        self.assertIsNone(case)

    def test_no_case_is_retrieved_when_http_500(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        m.get(
            f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            status_code=500,
        )

        case = fetch_single_case("d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d")

        self.assertIsNone(case)
