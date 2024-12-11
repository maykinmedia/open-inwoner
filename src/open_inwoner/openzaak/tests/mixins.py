from django.urls import reverse

from zgw_consumers.api_models.constants import (
    RolOmschrijving,
    RolTypes,
    VertrouwelijkheidsAanduidingen,
)
from zgw_consumers.constants import APITypes
from zgw_consumers.test import generate_oas_component, mock_service_oas_get

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.cms.cases.views.status import SimpleFile
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.tests.factories import ServiceFactory
from open_inwoner.openzaak.tests.shared import (
    CATALOGI_ROOT,
    DOCUMENTEN_ROOT,
    ZAKEN_ROOT,
)
from open_inwoner.utils.test import paginated_response


class ZakenTestMixin:
    """
    Create data required for tests that interact with the Zaken API:
        - digid user
        - services (catalogi, documenti)
        - zaken (including zaak type, status, rol)

    Note: the inheriting class must be decorated with `requests_mock.Mocker()`
          in order for the call to `setUpMocks` to work
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
        cls.document_service = ServiceFactory(
            api_root=DOCUMENTEN_ROOT, api_type=APITypes.drc
        )
        # openzaak config
        cls.config = OpenZaakConfig.get_solo()
        cls.config.zaak_service = cls.zaak_service
        cls.config.catalogi_service = cls.catalogi_service
        cls.config.document_service = cls.document_service
        cls.config.document_max_confidentiality = (
            VertrouwelijkheidsAanduidingen.beperkt_openbaar
        )
        cls.config.zaak_max_confidentiality = (
            VertrouwelijkheidsAanduidingen.beperkt_openbaar
        )
        cls.config.save()

        cls.case_detail_url = reverse(
            "cases:case_detail_content",
            kwargs={"object_id": "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d"},
        )

        # openzaak resources
        cls.zaak = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            uuid="d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            url=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/0caa29cb-0167-426f-8dc1-88bebd7c8804",
            identificatie="ZAAK-2022-0000000024",
            omschrijving="Coffee zaak 1",
            startdatum="2022-01-02",
            einddatumGepland="2022-01-04",
            uiterlijkeEinddatumAfdoening="2022-01-05",
            status=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
            resultaat=f"{ZAKEN_ROOT}resultaten/a44153aa-ad2c-6a07-be75-15add5113",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        cls.zaak_invisible = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            uuid="213b0a04-fcbc-4fee-8d11-cf950a0a0bbb",
            url=f"{ZAKEN_ROOT}zaken/213b0a04-fcbc-4fee-8d11-cf950a0a0bbb",
            zaaktype=cls.zaak["zaaktype"],
            identificatie="ZAAK-2022-invisible",
            omschrijving="Zaak invisible",
            startdatum="2022-01-02",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.geheim,
        )

        # additional zaken
        cls.zaak2 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/e4d469b9-6666-4bdd-bf42-b53445298102",
            uuid="e4d469b9-6666-4bdd-bf42-b53445298102",
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/0caa29cb-0167-426f-8dc1-88bebd7c8804",
            # zaaktype=cls.zaaktype["url"],
            identificatie="ZAAK-2022-0008800002",
            omschrijving="Coffee zaak 2",
            startdatum="2022-01-12",
            einddatum=None,
            status=f"{ZAKEN_ROOT}statussen/3da81560-c7fc-476a-ad13-beu760sle929",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        # closed
        cls.zaak3 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/6f8de38f-85ea-42d3-978c-845a033335a7",
            uuid="6f8de38f-85ea-42d3-978c-845a033335a7",
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/0caa29cb-0167-426f-8dc1-88bebd7c8804",
            # zaaktype=cls.zaaktype["url"],
            identificatie="ZAAK-2022-0001000003",
            omschrijving="Coffee zaak closed",
            startdatum="2021-07-26",
            einddatum="2022-01-16",
            status=f"{ZAKEN_ROOT}statussen/98659876-bbb3-476a-ad13-n3nvcght758js",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )

        cls.zaaktype = generate_oas_component(
            "ztc",
            "schemas/ZaakType",
            uuid="0caa29cb-0167-426f-8dc1-88bebd7c8804",
            url=cls.zaak["zaaktype"],
            identificatie="ZAAKTYPE-2020-0000000001",
            omschrijving="Coffee zaaktype",
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            doel="Ask for coffee",
            aanleiding="Coffee is essential",
            indicatieInternOfExtern="extern",
            handelingInitiator="Request",
            onderwerp="Coffee",
            handelingBehandelaar="Behandelen",
            opschortingEnAanhoudingMogelijk=False,
            verlengingMogelijk=False,
            publicatieIndicatie=False,
            besluittypen=[],
            beginGeldigheid="2020-09-25",
            versiedatum="2020-09-25",
        )
        cls.status_new = generate_oas_component(
            "zrc",
            "schemas/Status",
            url=f"{ZAKEN_ROOT}statussen/3da81560-c7fc-476a-ad13-beu760sle929",
            zaak=cls.zaak["url"],
            statustype=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-777yu878km09",
            datumStatusGezet="2021-01-12",
            statustoelichting="",
        )
        cls.status_finish = generate_oas_component(
            "zrc",
            "schemas/Status",
            url=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
            zaak=cls.zaak["url"],
            statustype=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-744516671fe4",
            datumStatusGezet="2021-03-12",
            statustoelichting="",
        )
        cls.status_type_new = generate_oas_component(
            "ztc",
            "schemas/StatusType",
            url=cls.status_new["statustype"],
            zaaktype=cls.zaaktype["url"],
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            omschrijving="Initial request",
            omschrijvingGeneriek="some content",
            statustekst="",
            volgnummer=1,
            isEindstatus=False,
        )
        cls.status_type_finish = generate_oas_component(
            "ztc",
            "schemas/StatusType",
            url=cls.status_finish["statustype"],
            zaaktype=cls.zaaktype["url"],
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            omschrijving="Finish",
            omschrijvingGeneriek="some content",
            statustekst="",
            volgnummer=2,
            isEindstatus=False,
        )
        cls.user_role = generate_oas_component(
            "zrc",
            "schemas/Rol",
            url=f"{ZAKEN_ROOT}rollen/f33153aa-ad2c-4a07-ae75-15add5891",
            omschrijvingGeneriek=RolOmschrijving.initiator,
            betrokkeneType=RolTypes.natuurlijk_persoon,
            betrokkeneIdentificatie={
                "inpBsn": "900222086",
                "voornamen": "Foo Bar",
                "voorvoegselGeslachtsnaam": "van der",
                "geslachtsnaam": "Bazz",
            },
        )
        cls.not_initiator_role = generate_oas_component(
            "zrc",
            "schemas/Rol",
            url=f"{ZAKEN_ROOT}rollen/aa353aa-ad2c-4a07-ae75-15add5822",
            omschrijvingGeneriek=RolOmschrijving.behandelaar,
            betrokkeneType=RolTypes.natuurlijk_persoon,
            betrokkeneIdentificatie={
                "inpBsn": "123456789",
                "voornamen": "Somebody",
                "geslachtsnaam": "Else",
            },
        )
        cls.result = generate_oas_component(
            "zrc",
            "schemas/Resultaat",
            uuid="a44153aa-ad2c-6a07-be75-15add5113",
            url=cls.zaak["resultaat"],
            resultaattype=f"{CATALOGI_ROOT}resultaattypen/b1a268dd-4322-47bb-a930-b83066b4a32c",
            zaak=cls.zaak["url"],
            toelichting="resultaat toelichting",
        )
        cls.zaak_informatie_object = generate_oas_component(
            "zrc",
            "schemas/ZaakInformatieObject",
            url=f"{ZAKEN_ROOT}zaakinformatieobjecten/e55153aa-ad2c-4a07-ae75-15add57d6",
            informatieobject=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812",
            zaak=cls.zaak["url"],
            aardRelatieWeergave="some content",
            titel="",
            beschrijving="",
            registratiedatum="2021-01-12",
        )
        cls.informatie_object_type = generate_oas_component(
            "ztc",
            "schemas/InformatieObjectType",
            url=f"{CATALOGI_ROOT}informatieobjecttype/014c38fe-b010-4412-881c-3000032fb321",
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            omschrijving="Some content",
        )
        cls.zaaktype_informatie_object_type = generate_oas_component(
            "ztc",
            "schemas/ZaakTypeInformatieObjectType",
            uuid="3fb03882-f6f9-4e0d-ad92-f810e24b9abb",
            url=f"{CATALOGI_ROOT}zaaktype-informatieobjecttypen/93250e6d-ef92-4474-acca-a6dbdcd61b7e",
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            zaaktype=cls.zaaktype["url"],
            informatieobjecttype=cls.informatie_object_type["url"],
            volgnummer=1,
            richting="inkomend",
            statustype=cls.status_type_finish,
        )
        cls.informatie_object = generate_oas_component(
            "drc",
            "schemas/EnkelvoudigInformatieObject",
            uuid="014c38fe-b010-4412-881c-3000032fb812",
            url=cls.zaak_informatie_object["informatieobject"],
            inhoud=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812/download",
            informatieobjecttype=cls.informatie_object_type["url"],
            status="definitief",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            bestandsnaam="uploaded_document.txt",
            titel="uploaded_document_title.txt",
            bestandsomvang=123,
        )
        cls.uploaded_informatie_object = generate_oas_component(
            "drc",
            "schemas/EnkelvoudigInformatieObject",
            uuid="85079ba3-554a-450f-b963-2ce20b176c90",
            url=cls.zaak_informatie_object["informatieobject"],
            inhoud=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/85079ba3-554a-450f-b963-2ce20b176c90/download",
            informatieobjecttype=cls.informatie_object_type["url"],
            status="definitief",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            bestandsnaam="upload.txt",
            bestandsomvang=123,
        )

        cls.zaak_informatie_object_invisible = generate_oas_component(
            "zrc",
            "schemas/ZaakInformatieObject",
            url=f"{ZAKEN_ROOT}zaakinformatieobjecten/fa5153aa-ad2c-4a07-ae75-15add57ee",
            informatieobject=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/994c38fe-b010-4412-881c-3000032fb123",
            zaak=cls.zaak_invisible["url"],
            aardRelatieWeergave="some invisible content",
            titel="",
            beschrijving="",
            registratiedatum="2021-01-12",
        )
        cls.informatie_object_invisible = generate_oas_component(
            "drc",
            "schemas/EnkelvoudigInformatieObject",
            uuid="994c38fe-b010-4412-881c-3000032fb123",
            url=cls.zaak_informatie_object_invisible["informatieobject"],
            inhoud=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/994c38fe-b010-4412-881c-3000032fb123/download",
            informatieobjecttype=cls.informatie_object_type["url"],
            status="definitief",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.geheim,
            bestandsnaam="geheim-document.txt",
            bestandsomvang=123,
        )

        cls.informatie_object_file = SimpleFile(
            name="uploaded_document_title.txt",
            size=123,
            url=reverse(
                "cases:document_download",
                kwargs={
                    "object_id": cls.zaak["uuid"],
                    "info_id": cls.informatie_object["uuid"],
                },
            ),
        )

    def _setUpOASMocks(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        mock_service_oas_get(m, DOCUMENTEN_ROOT, "drc")

    def setUpMocks(self, m):
        self._setUpOASMocks(m)

        from furl import furl

        m.get(
            furl(f"{ZAKEN_ROOT}zaken")
            .add(
                {
                    "rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn": self.user.bsn,
                    "maximaleVertrouwelijkheidaanduiding": VertrouwelijkheidsAanduidingen.beperkt_openbaar,
                }
            )
            .url,
            json=paginated_response([self.zaak, self.zaak2]),
        )

        for resource in [
            self.zaak,
            self.result,
            self.zaaktype,
            self.informatie_object_type,
            self.informatie_object,
            self.informatie_object_invisible,
            self.zaaktype_informatie_object_type,
            self.status_type_new,
            self.status_type_finish,
        ]:
            m.get(resource["url"], json=resource)

        m.post(
            f"{ZAKEN_ROOT}zaakinformatieobjecten",
            status_code=201,
            json=self.zaak_informatie_object,
        )

        # Zaak #1 (info_object, status, rol)
        m.get(
            f"{ZAKEN_ROOT}zaakinformatieobjecten?zaak={self.zaak['url']}",
            json=[self.zaak_informatie_object, self.zaak_informatie_object_invisible],
        )
        m.get(
            f"{ZAKEN_ROOT}statussen?zaak={self.zaak['url']}",
            # Taiga #972 these have to be oldest-last (newest-first) and cannot be resorted on
            json=paginated_response([self.status_finish, self.status_new]),
        )
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}",
            json=paginated_response([self.user_role, self.not_initiator_role]),
        )
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}&omschrijvingGeneriek={RolOmschrijving.initiator}",
            # Taiga #961 this is not an accurate OpenZaak response as it has a 'behandelaar' even when we filter on 'initiator'
            # but eSuite doesn't filter the response in the API, so we use filtering in Python to remove the not-initiator
            json=paginated_response([self.user_role, self.not_initiator_role]),
        )

        # other data
        m.post(
            f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten",
            status_code=201,
            json=self.uploaded_informatie_object,
        )
        m.get(
            f"{CATALOGI_ROOT}zaaktype-informatieobjecttypen?zaaktype={self.zaaktype['url']}&richting=inkomend",
            json=paginated_response([self.zaaktype_informatie_object_type]),
        )
        m.get(
            f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812/download",
            text="document content",
        )

    def setUpMocksExtra(self, m):
        for resource in [
            self.zaak2,
            self.zaak3,
        ]:
            m.get(resource["url"], json=resource)

        # Zaak #2 (info_object, status, rol)
        m.get(
            f"{ZAKEN_ROOT}zaakinformatieobjecten?zaak={self.zaak2['url']}",
            json=[self.zaak_informatie_object, self.zaak_informatie_object_invisible],
        )
        m.get(
            f"{ZAKEN_ROOT}statussen?zaak={self.zaak2['url']}",
            # Taiga #972 these have to be oldest-last (newest-first) and cannot be resorted on
            json=paginated_response([self.status_finish, self.status_new]),
        )
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak2['url']}",
            json=paginated_response([self.user_role, self.not_initiator_role]),
        )
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak2['url']}&omschrijvingGeneriek={RolOmschrijving.initiator}",
            json=paginated_response([self.user_role, self.not_initiator_role]),
        )

        # Zaak #3 (info_object, status, rol)
        m.get(
            f"{ZAKEN_ROOT}zaakinformatieobjecten?zaak={self.zaak3['url']}",
            json=[self.zaak_informatie_object, self.zaak_informatie_object_invisible],
        )
        m.get(
            f"{ZAKEN_ROOT}statussen?zaak={self.zaak3['url']}",
            # Taiga #972 these have to be oldest-last (newest-first) and cannot be resorted on
            json=paginated_response([self.status_finish, self.status_new]),
        )
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak3['url']}",
            json=paginated_response([self.user_role, self.not_initiator_role]),
        )
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak3['url']}&omschrijvingGeneriek={RolOmschrijving.initiator}",
            json=paginated_response([self.user_role, self.not_initiator_role]),
        )
