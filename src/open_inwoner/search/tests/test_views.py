from urllib.parse import urlencode

from django.test import TestCase, override_settings, tag
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import requests_mock
from furl import furl
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen
from zgw_consumers.constants import APITypes
from zgw_consumers.test import generate_oas_component, mock_service_oas_get

from open_inwoner.accounts.tests.factories import DigidUserFactory
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.tests.factories import ServiceFactory
from open_inwoner.openzaak.tests.shared import CATALOGI_ROOT, ZAKEN_ROOT
from open_inwoner.utils.test import paginated_response

from .utils import ESMixin


@requests_mock.Mocker()
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
@tag("elastic")
class TestSearchView(ESMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = DigidUserFactory(bsn="900222086", email="johm@smith.nl")
        cls.user2 = DigidUserFactory(bsn="123456782", email="jane@doe.nl")
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
                    "identificatie": "ZAAK-2022-0000000001",
                }
            )
            .url,
            json=paginated_response([self.zaak1]),
        )
        m.get(
            furl(f"{ZAKEN_ROOT}zaken")
            .add(
                {
                    "rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn": self.user2.bsn,
                    "maximaleVertrouwelijkheidaanduiding": VertrouwelijkheidsAanduidingen.beperkt_openbaar,
                    "identificatie": "ZAAK-2022-0000000001",
                }
            )
            .url,
            json=paginated_response([]),
        )
        m.get(
            furl(f"{ZAKEN_ROOT}zaken")
            .add(
                {
                    "rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn": self.user.bsn,
                    "maximaleVertrouwelijkheidaanduiding": VertrouwelijkheidsAanduidingen.beperkt_openbaar,
                    "identificatie": "ZAAK-2022-000000000",
                }
            )
            .url,
            json=paginated_response([]),
        )
        for resource in [
            self.zaaktype,
            self.status_type1,
            self.status_type2,
            self.status1,
            self.status2,
        ]:
            m.get(resource["url"], json=resource)

    def test_search_hidden_from_anonymous_users(self, m):
        config = SiteConfiguration.get_solo()
        config.hide_categories_from_anonymous_users = True
        config.save()

        response = self.client.get(reverse("search:search"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/accounts/login/?next=/search/")

    def test_search_not_hidden_from_anonymous_users(self, m):
        config = SiteConfiguration.get_solo()
        config.hide_categories_from_anonymous_users = False
        config.save()

        response = self.client.get(reverse("search:search"))

        self.assertEqual(response.status_code, 200)

    def test_search_case_identificatie_success(self, m):
        self._setUpMocks(m)

        self.client.force_login(self.user)
        params = urlencode({"query": "ZAAK-2022-0000000001"}, doseq=True)
        response = self.client.get(f'{reverse("search:search")}?{params}')

        # In case of an exact identificatie match, user should be redirected to
        # the status page of that Zaak
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse(
                "cases:case_detail",
                kwargs={"object_id": "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d"},
            ),
        )

    def test_search_case_identificatie_case_does_not_belong_to_user(self, m):
        self._setUpMocks(m)

        self.client.force_login(self.user2)
        params = urlencode({"query": "ZAAK-2022-0000000001"}, doseq=True)
        response = self.client.get(f'{reverse("search:search")}?{params}')

        # Show regular search results page
        self.assertEqual(response.status_code, 200)

    def test_search_case_identificatie_no_exact_match(self, m):
        self._setUpMocks(m)

        self.client.force_login(self.user)
        params = urlencode({"query": "ZAAK-2022-000000000"}, doseq=True)
        response = self.client.get(f'{reverse("search:search")}?{params}')

        # Show regular search results page
        self.assertEqual(response.status_code, 200)

    def test_search_case_identificatie_cache(self, m):
        self._setUpMocks(m)

        self.client.force_login(self.user)
        params = urlencode({"query": "ZAAK-2022-0000000001"}, doseq=True)
        response = self.client.get(f'{reverse("search:search")}?{params}')

        # In case of an exact identificatie match, user should be redirected to
        # the status page of that Zaak
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse(
                "cases:case_detail",
                kwargs={"object_id": "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d"},
            ),
        )

        # Search with different query should not use cached result from previous search
        params = urlencode({"query": "ZAAK-2022-000000000"}, doseq=True)
        response = self.client.get(f'{reverse("search:search")}?{params}')

        # Show regular search results page
        self.assertEqual(response.status_code, 200)
