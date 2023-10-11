from furl import furl
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen
from zgw_consumers.constants import APITypes
from zgw_consumers.test import generate_oas_component, mock_service_oas_get

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.tests.factories import ServiceFactory
from open_inwoner.openzaak.tests.shared import CATALOGI_ROOT, ZAKEN_ROOT
from open_inwoner.utils.test import paginated_response


class ZakenTestMixin:
    """
    Set up data required by tests that interact with the Zaken API:
        - digid user
        - services (zaken, catalogi)
        - zaken, zaak types, status types
        - request mocks

    Note: the inheriting class must be decorated with requests_mock.Mocker() to make
          the call to _setUpMocks work
    """

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
        cls.zaak_type_intern = generate_oas_component(
            "ztc",
            "schemas/ZaakType",
            url=f"{CATALOGI_ROOT}zaaktypen/53340e34-75a1-4b04-1234",
            omschrijving="Intern zaaktype",
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            indicatieInternOfExtern="intern",
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
        # open
        cls.zaak1 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            uuid="d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            zaaktype=cls.zaaktype["url"],
            identificatie="ZAAK-2022-0000000001",
            omschrijving="Coffee zaak 1",
            startdatum="2022-01-02",
            einddatum=None,
            status=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        cls.status1 = generate_oas_component(
            "zrc",
            "schemas/Status",
            url=cls.zaak1["status"],
            zaak=cls.zaak1["url"],
            statustype=cls.status_type1["url"],
            datumStatusGezet="2021-01-12",
            statustoelichting="",
        )
        cls.zaak2 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/e4d469b9-6666-4bdd-bf42-b53445298102",
            uuid="e4d469b9-6666-4bdd-bf42-b53445298102",
            zaaktype=cls.zaaktype["url"],
            identificatie="ZAAK-2022-0008800002",
            omschrijving="Coffee zaak 2",
            startdatum="2022-01-12",
            einddatum=None,
            status=f"{ZAKEN_ROOT}statussen/3da81560-c7fc-476a-ad13-beu760sle929",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        cls.status2 = generate_oas_component(
            "zrc",
            "schemas/Status",
            url=cls.zaak2["status"],
            zaak=cls.zaak2["url"],
            statustype=cls.status_type1["url"],
            datumStatusGezet="2021-03-12",
            statustoelichting="",
        )
        # closed
        cls.zaak3 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/6f8de38f-85ea-42d3-978c-845a033335a7",
            uuid="6f8de38f-85ea-42d3-978c-845a033335a7",
            zaaktype=cls.zaaktype["url"],
            identificatie="ZAAK-2022-0001000003",
            omschrijving="Coffee zaak closed",
            startdatum="2021-07-26",
            einddatum="2022-01-16",
            status=f"{ZAKEN_ROOT}statussen/98659876-bbb3-476a-ad13-n3nvcght758js",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        cls.status3 = generate_oas_component(
            "zrc",
            "schemas/Status",
            url=cls.zaak3["status"],
            zaak=cls.zaak3["url"],
            statustype=cls.status_type2["url"],
            datumStatusGezet="2021-03-15",
            statustoelichting="",
        )
        # not visible
        cls.zaak_intern = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4ee0bf67d",
            uuid="d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            zaaktype=cls.zaak_type_intern["url"],
            identificatie="ZAAK-2022-0000000009",
            omschrijving="Intern zaak",
            startdatum="2022-01-02",
            einddatum=None,
            status=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c90234500333",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        cls.status_intern = generate_oas_component(
            "zrc",
            "schemas/Status",
            url=cls.zaak_intern["status"],
            zaak=cls.zaak_intern["url"],
            statustype=cls.status_type1["url"],
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
            json=paginated_response(
                [self.zaak1, self.zaak2, self.zaak3, self.zaak_intern]
            ),
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
