import datetime

from django.core.cache import cache
from django.test.utils import override_settings
from django.urls import reverse_lazy

import requests_mock
from django_webtest import WebTest
from freezegun import freeze_time
from furl import furl
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen
from zgw_consumers.constants import APITypes
from zgw_consumers.test import generate_oas_component, mock_service_oas_get

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.utils.test import ClearCachesMixin, paginated_response

from ..models import OpenZaakConfig
from .factories import ServiceFactory
from .shared import CATALOGI_ROOT, ZAKEN_ROOT


@requests_mock.Mocker()
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class OpenCaseListCacheTests(ClearCachesMixin, WebTest):
    inner_url = reverse_lazy("cases:open_cases_content")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = UserFactory(
            login_type=LoginTypeChoices.digid, bsn="900222086", email="johm@smith.nl"
        )
        # services
        cls.zaak_service = ServiceFactory(api_root=ZAKEN_ROOT, api_type=APITypes.zrc)
        cls.catalogi_service = ServiceFactory(
            api_root=CATALOGI_ROOT, api_type=APITypes.ztc
        )
        # openzaak config
        cls.config = OpenZaakConfig.get_solo()
        cls.config.zaak_service = cls.zaak_service
        cls.config.catalogi_service = cls.catalogi_service
        cls.config.zaak_max_confidentiality = (
            VertrouwelijkheidsAanduidingen.beperkt_openbaar
        )
        cls.config.save()

        cls.zaaktype = generate_oas_component(
            "ztc",
            "schemas/ZaakType",
            url=f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f",
            omschrijving="Coffee zaaktype",
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            indicatieInternOfExtern="extern",
        )
        cls.status_type1 = generate_oas_component(
            "ztc",
            "schemas/StatusType",
            url=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-777yu878km09",
            zaaktype=cls.zaaktype["url"],
            omschrijving="Initial request",
            volgnummer=1,
            isEindstatus=False,
        )
        cls.status_type2 = generate_oas_component(
            "ztc",
            "schemas/StatusType",
            url=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-744516671fe4",
            zaaktype=cls.zaaktype["url"],
            omschrijving="Finish",
            volgnummer=2,
            isEindstatus=True,
        )
        cls.zaak1 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            zaaktype=cls.zaaktype["url"],
            identificatie="ZAAK-2022-0000000001",
            omschrijving="Coffee zaak1",
            startdatum="2022-01-02",
            einddatum=None,
            status=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        cls.status1 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}statussen/3da81560-c7fc-476a-ad13-beu760sle929",
            zaak=cls.zaak1["url"],
            statustype=cls.status_type1["url"],
            datumStatusGezet="2021-01-12",
            statustoelichting="",
        )
        cls.zaak2 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/e4d469b9-6666-4bdd-bf42-b53445298102",
            zaaktype=cls.zaaktype["url"],
            identificatie="ZAAK-2022-0008800002",
            omschrijving="Coffee zaak2",
            startdatum="2022-01-12",
            einddatum=None,
            status=f"{ZAKEN_ROOT}statussen/3da81560-c7fc-476a-ad13-beu760sle929",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        cls.status2 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
            zaak=cls.zaak2["url"],
            statustype=cls.status_type2["url"],
            datumStatusGezet="2021-03-12",
            statustoelichting="",
        )

        # objects needed to test how the cache is updated
        cls.new_zaaktype = generate_oas_component(
            "ztc",
            "schemas/ZaakType",
            url=f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f-98ui7y87i876",
            omschrijving="Tea zaaktype",
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            indicatieInternOfExtern="extern",
        )
        cls.new_status_type = generate_oas_component(
            "ztc",
            "schemas/StatusType",
            url=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-984yr8887rhe",
            zaaktype=cls.new_zaaktype["url"],
            omschrijving="Process",
            volgnummer=1,
            isEindstatus=False,
        )
        cls.new_zaak = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/a25b2dce-1cae-4fc9-b9e9-141b0ad5189f",
            zaaktype=cls.new_zaaktype["url"],
            identificatie="ZAAK-2022-0000000003",
            omschrijving="Tea zaak",
            startdatum="2022-01-02",
            einddatum=None,
            status=f"{ZAKEN_ROOT}statussen/3da81560-c7fc-476a-ad13-oie8u899923g",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        cls.new_status = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}statussen/3da81560-c7fc-476a-ad13-oie8u899923g",
            zaak=cls.new_zaak["url"],
            statustype=cls.new_status_type["url"],
            datumStatusGezet="2021-01-12",
            statustoelichting="",
        )

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
            json=paginated_response([self.zaak1, self.zaak2]),
        )
        for resource in [
            self.zaaktype,
            self.status_type1,
            self.status_type2,
            self.status1,
            self.status2,
        ]:
            m.get(resource["url"], json=resource)

    def _setUpNewMock(self, m):
        m.get(
            f"{ZAKEN_ROOT}zaken?rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn=900222086",
            json=paginated_response([self.zaak1, self.zaak2, self.new_zaak]),
        )
        for new_resource in [
            self.new_zaaktype,
            self.new_status,
            self.status_type1,
            self.status_type2,
            self.new_status_type,
        ]:
            m.get(new_resource["url"], json=new_resource)

    def test_case_types_are_cached(self, m):
        self._setUpMocks(m)

        # Cache is empty before the request
        self.assertIsNone(cache.get(f"case_type:{self.zaaktype['url']}"))

        self.app.get(self.inner_url, user=self.user, headers={"HX-Request": "true"})

        # Case type is cached after the request
        self.assertIsNotNone(cache.get(f"case_type:{self.zaaktype['url']}"))

    def test_cached_case_types_are_deleted_after_one_day(self, m):
        self._setUpMocks(m)

        with freeze_time("2022-01-01 12:00") as frozen_time:
            self.app.get(self.inner_url, user=self.user, headers={"HX-Request": "true"})

            # After one day the results should be deleted
            frozen_time.tick(delta=datetime.timedelta(days=1))
            self.assertIsNone(cache.get(f"case_type:{self.zaaktype['url']}"))

    def test_cached_case_types_in_combination_with_new_ones(self, m):
        self._setUpMocks(m)

        with freeze_time("2022-01-01 12:00") as frozen_time:
            # First attempt
            self.assertIsNone(cache.get(f"case_type:{self.zaaktype['url']}"))

            self.app.get(self.inner_url, user=self.user, headers={"HX-Request": "true"})

            self.assertIsNotNone(cache.get(f"case_type:{self.zaaktype['url']}"))

            # Second attempt with new case and case type
            self._setUpNewMock(m)
            # Wait 3 minutes for the list cases cache to expire
            frozen_time.tick(delta=datetime.timedelta(minutes=3))
            self.assertIsNone(cache.get(f"case_type:{self.new_zaaktype['url']}"))

            self.app.get(self.inner_url, user=self.user, headers={"HX-Request": "true"})

            self.assertIsNotNone(cache.get(f"case_type:{self.zaaktype['url']}"))
            self.assertIsNotNone(cache.get(f"case_type:{self.new_zaaktype['url']}"))

    def test_cached_status_types_are_deleted_after_one_day(self, m):
        self._setUpMocks(m)

        with freeze_time("2022-01-01 12:00") as frozen_time:
            self.app.get(self.inner_url, user=self.user, headers={"HX-Request": "true"})

            # After one day the results should be deleted
            frozen_time.tick(delta=datetime.timedelta(hours=24))
            self.assertIsNone(
                cache.get(f"status_types_for_case_type:{self.zaaktype['url']}")
            )
            self.assertIsNone(
                cache.get(f"status_types_for_case_type:{self.zaaktype['url']}")
            )

    def test_statuses_are_cached(self, m):
        self._setUpMocks(m)

        # Cache is empty before the request
        self.assertIsNone(cache.get(f"status:{self.status1['url']}"))
        self.assertIsNone(cache.get(f"status:{self.status2['url']}"))

        self.app.get(self.inner_url, user=self.user, headers={"HX-Request": "true"})

        # Status is cached after the request
        self.assertIsNotNone(cache.get(f"status:{self.status1['url']}"))
        self.assertIsNotNone(cache.get(f"status:{self.status2['url']}"))

    def test_cached_statuses_are_deleted_after_one_hour(self, m):
        self._setUpMocks(m)

        with freeze_time("2022-01-01 12:00") as frozen_time:
            self.app.get(self.inner_url, user=self.user, headers={"HX-Request": "true"})

            # After one hour the results should be deleted
            frozen_time.tick(delta=datetime.timedelta(hours=1))
            self.assertIsNone(cache.get(f"status:{self.status1['url']}"))
            self.assertIsNone(cache.get(f"status:{self.status2['url']}"))

    def test_cached_statuses_in_combination_with_new_ones(self, m):
        self._setUpMocks(m)

        with freeze_time("2022-01-01 12:00") as frozen_time:
            # First attempt
            self.assertIsNone(cache.get(f"status:{self.status1['url']}"))
            self.assertIsNone(cache.get(f"status:{self.status2['url']}"))

            self.app.get(self.inner_url, user=self.user, headers={"HX-Request": "true"})

            self.assertIsNotNone(cache.get(f"status:{self.status1['url']}"))
            self.assertIsNotNone(cache.get(f"status:{self.status2['url']}"))

            # Second attempt with new case and status type
            self._setUpNewMock(m)
            # Wait 3 minutes for the list cases cache to expire
            frozen_time.tick(delta=datetime.timedelta(minutes=3))
            self.assertIsNone(cache.get(f"status:{self.new_status['url']}"))

            self.app.get(self.inner_url, user=self.user, headers={"HX-Request": "true"})

            self.assertIsNotNone(cache.get(f"status:{self.new_status['url']}"))
            self.assertIsNotNone(cache.get(f"status:{self.status1['url']}"))
            self.assertIsNotNone(cache.get(f"status:{self.status2['url']}"))


class ClosedCaseListCacheTests(OpenCaseListCacheTests):
    """
    run the same tests as for open cases
    """

    inner_url = reverse_lazy("cases:closed_cases_content")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        for zaak in [cls.zaak1, cls.zaak2, cls.new_zaak]:
            zaak["einddatum"] = "2022-01-16"
