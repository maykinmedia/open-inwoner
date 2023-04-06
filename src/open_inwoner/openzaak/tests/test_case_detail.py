import datetime
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import requests_mock
from django_webtest import WebTest
from timeline_logger.models import TimelineLog
from webtest import Upload
from webtest.forms import Hidden
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.constants import (
    RolOmschrijving,
    RolTypes,
    VertrouwelijkheidsAanduidingen,
)
from zgw_consumers.constants import APITypes
from zgw_consumers.test import generate_oas_component, mock_service_oas_get

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.accounts.views.cases import SimpleFile
from open_inwoner.openzaak.tests.factories import (
    ZaakTypeConfigFactory,
    ZaakTypeInformatieObjectTypeConfigFactory,
)
from open_inwoner.utils.test import ClearCachesMixin, paginated_response

from ..api_models import Status, StatusType
from ..models import OpenZaakConfig
from ..utils import format_zaak_identificatie
from .factories import CatalogusConfigFactory, ServiceFactory
from .shared import CATALOGI_ROOT, DOCUMENTEN_ROOT, ZAKEN_ROOT


@requests_mock.Mocker()
class TestCaseDetailView(ClearCachesMixin, WebTest):
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
            "accounts:case_status",
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
            omschrijving="Zaak naar aanleiding van ingezonden formulier",
            startdatum="2022-01-02",
            einddatum="2022-01-03",
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
            bestandsnaam="document.txt",
            titel="document_title.txt",
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
            name="document_title.txt",
            size=123,
            url=reverse(
                "accounts:case_document_download",
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

    def _setUpMocks(self, m):
        self._setUpOASMocks(m)

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

    def test_status_is_retrieved_when_user_logged_in_via_digid(self, m):
        self._setUpMocks(m)
        status_new_obj, status_finish_obj = factory(
            Status, [self.status_new, self.status_finish]
        )
        status_new_obj.statustype = factory(StatusType, self.status_type_new)
        status_finish_obj.statustype = factory(StatusType, self.status_type_finish)

        response = self.app.get(self.case_detail_url, user=self.user)

        self.assertEqual(
            response.context.get("case"),
            {
                "identification": "ZAAK-2022-0000000024",
                "start_date": datetime.date(2022, 1, 2),
                "end_date": datetime.date(2022, 1, 3),
                "end_date_planned": datetime.date(2022, 1, 4),
                "end_date_legal": datetime.date(2022, 1, 5),
                "description": "Zaak naar aanleiding van ingezonden formulier",
                "current_status": "Finish",
                "statuses": [status_new_obj, status_finish_obj],
                # only one visible information object
                "documents": [self.informatie_object_file],
                "initiator": "Foo Bar van der Bazz",
                "result": "resultaat toelichting",
                "case_type_config_description": "",
                "internal_upload_enabled": False,
                "external_upload_enabled": False,
                "external_upload_url": "",
                "allowed_file_extensions": sorted(self.config.allowed_file_extensions),
            },
        )

    def test_page_displays_expected_data(self, m):
        self._setUpMocks(m)

        response = self.app.get(self.case_detail_url, user=self.user)

        self.assertContains(response, "ZAAK-2022-0000000024")
        self.assertContains(response, "Zaak naar aanleiding van ingezonden formulier")
        self.assertContains(response, "Finish")
        self.assertContains(response, "document")
        self.assertContains(response, "Foo Bar van der Bazz")
        self.assertContains(response, "resultaat toelichting")

    def test_page_reformats_zaak_identificatie(self, m):
        self._setUpMocks(m)

        with patch(
            "open_inwoner.accounts.views.cases.format_zaak_identificatie",
            wraps=format_zaak_identificatie,
        ) as spy_format:
            self.app.get(self.case_detail_url, user=self.user)

        spy_format.assert_called_once()

    def test_when_accessing_case_detail_a_timelinelog_is_created(self, m):
        self._setUpMocks(m)

        self.app.get(self.case_detail_url, user=self.user)

        log = TimelineLog.objects.last()
        self.assertIn(self.zaak["identificatie"], log.extra_data["message"])
        self.assertEqual(self.user, log.user)
        self.assertEqual(self.user, log.content_object)

    def test_current_status_in_context_is_the_most_recent_one(self, m):
        self._setUpMocks(m)

        response = self.app.get(self.case_detail_url, user=self.user)
        current_status = response.context.get("case", {}).get("current_status")
        self.assertEquals(current_status, "Finish")

    def test_case_io_objects_are_retrieved_when_user_logged_in_via_digid(self, m):
        self._setUpMocks(m)

        response = self.app.get(self.case_detail_url, user=self.user)
        documents = response.context.get("case", {}).get("documents")
        self.assertEquals(len(documents), 1)
        self.assertEquals(
            documents,
            # only one visible information object
            [self.informatie_object_file],
        )

    def test_user_is_redirected_to_root_when_not_logged_in_via_digid(self, m):
        self._setUpMocks(m)

        user = UserFactory(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.default,
        )
        response = self.app.get(self.case_detail_url, user=user)

        self.assertRedirects(response, reverse("root"))

    def test_anonymous_user_has_no_access_to_status_page(self, m):
        self._setUpMocks(m)
        user = AnonymousUser()
        response = self.app.get(self.case_detail_url, user=user)

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('accounts:case_status', kwargs={'object_id': 'd8bbdeb7-770f-4ca9-b1ea-77b4730bf67d'})}",
        )

    def test_no_access_when_no_roles_are_found_for_user_bsn(self, m):
        self._setUpOASMocks(m)

        m.get(self.zaak["url"], json=self.zaak)
        m.get(self.zaaktype["url"], json=self.zaaktype)
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}",
            # no roles for our user found
            json=paginated_response([self.not_initiator_role]),
        )
        # m.get(
        #     f"{ZAKEN_ROOT}zaakinformatieobjecten?zaak={self.zaak['url']}",
        #     json=[self.zaak_informatie_object, self.zaak_informatie_object_invisible],
        # )
        # m.get(
        #     f"{ZAKEN_ROOT}statussen?zaak={self.zaak['url']}",
        #     json=paginated_response([self.status_finish, self.status_new]),
        # )
        response = self.app.get(self.case_detail_url, user=self.user)
        self.assertRedirects(response, reverse("root"))

    def test_no_data_is_retrieved_when_zaaktype_is_internal(self, m):
        self._setUpOASMocks(m)

        m.get(self.zaak["url"], json=self.zaak)
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}",
            # no roles for our user found
            json=paginated_response([self.user_role]),
        )
        zaaktype_intern = generate_oas_component(
            "ztc",
            "schemas/ZaakType",
            url=self.zaak["zaaktype"],
            indicatieInternOfExtern="intern",
        )
        m.get(self.zaaktype["url"], json=zaaktype_intern)
        self.app.get(self.informatie_object_file.url, user=self.user, status=403)

    def test_no_data_is_retrieved_when_http_404(self, m):
        self._setUpOASMocks(m)

        m.get(self.zaak["url"], status_code=404)

        response = self.app.get(self.case_detail_url, user=self.user)

        self.assertIsNone(response.context.get("case"))
        self.assertContains(response, _("There is no available data at the moment."))

    def test_no_data_is_retrieved_when_http_500(self, m):
        self._setUpOASMocks(m)

        m.get(self.zaak["url"], status_code=500)

        response = self.app.get(self.case_detail_url, user=self.user)

        self.assertIsNone(response.context.get("case"))
        self.assertContains(response, _("There is no available data at the moment."))

    def test_no_access_when_case_is_confidential(self, m):
        self._setUpOASMocks(m)

        m.get(self.zaak_invisible["url"], json=self.zaak_invisible)
        m.get(self.zaaktype["url"], json=self.zaaktype)
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak_invisible['url']}",
            json=paginated_response([self.user_role, self.not_initiator_role]),
        )

        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": self.zaak_invisible["uuid"]},
            ),
            user=self.user,
        )
        self.assertRedirects(response, reverse("root"))

    def test_single_expected_information_object_type_is_available_in_upload_form(
        self, m
    ):
        self._setUpMocks(m)

        zaak_type_config = ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
        )
        zaak_type_iotc = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url=self.informatie_object["url"],
            zaaktype_uuids=[self.zaaktype["uuid"]],
            document_upload_enabled=True,
        )

        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": self.zaak["uuid"]},
            ),
            user=self.user,
        )
        form = response.forms["document-upload"]
        type_field = form["type"]
        expected_choice = zaak_type_iotc.id

        self.assertEqual(type(type_field), Hidden)
        self.assertEqual(type_field.value, str(expected_choice))

    def test_expected_information_object_types_are_available_in_upload_form(self, m):
        self._setUpMocks(m)

        zaak_type_config = ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
        )
        zaak_type_iotc1 = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url=self.informatie_object["url"],
            zaaktype_uuids=[self.zaaktype["uuid"]],
            document_upload_enabled=True,
        )
        zaak_type_iotc2 = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/705364ff-385a-4d60-b0da-a8cf5d18e6bb",
            zaaktype_uuids=[self.zaaktype["uuid"]],
            document_upload_enabled=True,
        )

        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": self.zaak["uuid"]},
            ),
            user=self.user,
        )
        form = response.forms["document-upload"]
        type_field = form["type"]
        expected_choices = [
            (str(zaak_type_iotc1.id), False, zaak_type_iotc1.omschrijving),
            (str(zaak_type_iotc2.id), False, zaak_type_iotc2.omschrijving),
        ]

        self.assertEqual(sorted(type_field.options), sorted(expected_choices))

    def test_case_type_config_description_is_rendered_when_internal_upload(self, m):
        self._setUpMocks(m)

        zaak_type_config = ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
            external_document_upload_url="https://test.example.com",
            document_upload_enabled=True,
            description="some description content",
        )

        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": self.zaak["uuid"]},
            ),
            user=self.user,
        )

        self.assertContains(response, _("some description content"))

    def test_upload_form_is_not_rendered_when_no_case_exists(self, m):
        self._setUpMocks(m)

        m.get(self.zaak["url"], status_code=500)
        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": self.zaak["uuid"]},
            ),
            user=self.user,
        )

        self.assertNotIn("document-upload", response.forms)
        self.assertContains(response, _("There is no available data at the moment."))

    def test_upload_form_is_not_rendered_when_no_information_object_types_exist(
        self, m
    ):
        self._setUpMocks(m)

        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": self.zaak["uuid"]},
            ),
            user=self.user,
        )

        self.assertNotIn("document-upload", response.forms)

    def test_successful_document_upload_flow(self, m):
        self._setUpMocks(m)

        zaak_type_config = ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
        )
        zaak_type_iotc = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url=self.informatie_object["url"],
            zaaktype_uuids=[self.zaaktype["uuid"]],
            document_upload_enabled=True,
        )

        response = self.app.get(self.case_detail_url, user=self.user)
        form = response.forms["document-upload"]
        form["title"] = "uploaded file"
        form["type"] = zaak_type_iotc.id
        form["file"] = Upload("upload.txt", b"data", "text/plain")
        form_response = form.submit()

        redirect = form_response.follow()
        redirect_messages = list(redirect.context["messages"])

        self.assertRedirects(form_response, self.case_detail_url)
        self.assertEqual(
            redirect_messages[0].message,
            _(
                f"{self.uploaded_informatie_object['bestandsnaam']} is succesvol geüpload"
            ),
        )

    def test_successful_document_upload_flow_with_uppercase_extension(self, m):
        self._setUpMocks(m)

        zaak_type_config = ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
        )
        zaak_type_iotc = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url=self.informatie_object["url"],
            zaaktype_uuids=[self.zaaktype["uuid"]],
            document_upload_enabled=True,
        )

        response = self.app.get(self.case_detail_url, user=self.user)
        form = response.forms["document-upload"]
        form["title"] = "uploaded file"
        form["type"] = zaak_type_iotc.id
        form["file"] = Upload("upload.TXT", b"data", "text/plain")
        form_response = form.submit()

        redirect = form_response.follow()
        redirect_messages = list(redirect.context["messages"])

        self.assertRedirects(form_response, self.case_detail_url)
        self.assertEqual(
            redirect_messages[0].message,
            _("upload.TXT is succesvol geüpload"),
        )

    def test_upload_file_flow_fails_with_invalid_file_extension(self, m):
        self._setUpMocks(m)

        zaak_type_config = ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
        )
        zaak_type_iotc = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url=self.informatie_object["url"],
            zaaktype_uuids=[self.zaaktype["uuid"]],
            document_upload_enabled=True,
        )

        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": self.zaak["uuid"]},
            ),
            user=self.user,
        )
        form = response.forms["document-upload"]
        form["title"] = "uploaded file"
        form["type"] = zaak_type_iotc.id
        form["file"] = Upload("upload.xml", b"data", "application/xml")
        form_response = form.submit()

        self.assertEqual(
            form_response.context["form"].errors,
            {
                "file": [
                    f"Het type bestand dat u hebt geüpload is ongeldig. Geldige bestandstypen zijn: {', '.join(sorted(self.config.allowed_file_extensions))}"
                ]
            },
        )

    def test_upload_with_larger_file_size_fails(self, m):
        self._setUpMocks(m)

        zaak_type_config = ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
        )
        zaak_type_iotc = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url=self.informatie_object["url"],
            zaaktype_uuids=[self.zaaktype["uuid"]],
            document_upload_enabled=True,
        )

        # mock max file size to 10 bytes
        self.config.max_upload_size = 10 / (1024**2)
        self.config.save()

        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": self.zaak["uuid"]},
            ),
            user=self.user,
        )
        form = response.forms["document-upload"]

        form["title"] = "uploaded file"
        form["type"] = zaak_type_iotc.id
        form["file"] = Upload("upload.txt", b"data", "text/plain")
        form_response = form.submit()

        self.config.refresh_from_db()

        self.assertEqual(
            form_response.context["form"].errors,
            {
                "file": [
                    f"Een aangeleverd bestand dient maximaal {self.config.max_upload_size} MB te zijn, uw bestand is te groot."
                ]
            },
        )

    def test_external_upload_section_is_rendered(self, m):
        self._setUpMocks(m)

        zaak_type_config = ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
            external_document_upload_url="https://test.example.com",
            document_upload_enabled=True,
        )

        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": self.zaak["uuid"]},
            ),
            user=self.user,
        )

        self.assertContains(
            response,
            _("By clicking the button below you can upload a document."),
        )
        self.assertContains(response, zaak_type_config.external_document_upload_url)

    def test_case_type_config_description_is_rendered_when_external_upload(self, m):
        self._setUpMocks(m)

        zaak_type_config = ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
            external_document_upload_url="https://test.example.com",
            document_upload_enabled=True,
            description="some description content",
        )

        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": self.zaak["uuid"]},
            ),
            user=self.user,
        )

        self.assertContains(response, _("some description content"))

    def test_external_upload_section_is_not_rendered_when_upload_disabled(self, m):
        self._setUpMocks(m)

        zaak_type_config = ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
            external_document_upload_url="https://test.example.com",
        )

        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": self.zaak["uuid"]},
            ),
            user=self.user,
        )

        self.assertNotContains(
            response, _("By clicking the button below you can upload a document.")
        )
        self.assertNotContains(response, zaak_type_config.external_document_upload_url)

    def test_external_upload_section_is_not_rendered_when_no_url_specified(self, m):
        self._setUpMocks(m)

        ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
            external_document_upload_url="",
            document_upload_enabled=True,
        )

        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": self.zaak["uuid"]},
            ),
            user=self.user,
        )

        self.assertNotContains(
            response, _("By clicking the button below you can upload a document.")
        )

    def test_external_upload_section_is_not_rendered_when_upload_disabled_and_no_url_specified(
        self, m
    ):
        self._setUpMocks(m)

        ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
            external_document_upload_url="",
        )

        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": self.zaak["uuid"]},
            ),
            user=self.user,
        )

        self.assertNotContains(
            response, _("By clicking the button below you can upload a document.")
        )

    def test_request_error_in_uploading_document_shows_proper_message(self, m):
        self._setUpMocks(m)

        zaak_type_config = ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
        )
        ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url=self.informatie_object["url"],
            zaaktype_uuids=[self.zaaktype["uuid"]],
            document_upload_enabled=True,
        )

        m.post(f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten", status_code=500)

        response = self.app.get(self.case_detail_url, user=self.user)
        form = response.forms["document-upload"]
        form["title"] = "uploaded file"
        form["file"] = Upload("upload.txt", b"data", "text/plain")
        form_response = form.submit()

        form_response_messages = list(form_response.context["messages"])

        self.assertEqual(
            form_response_messages[0].message,
            _(
                f"Een fout is opgetreden bij het uploaden van {self.uploaded_informatie_object['bestandsnaam']}"
            ),
        )

    def test_request_error_in_connecting_doc_with_zaak_shows_proper_message(self, m):
        self._setUpMocks(m)

        zaak_type_config = ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
        )
        ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url=self.informatie_object["url"],
            zaaktype_uuids=[self.zaaktype["uuid"]],
            document_upload_enabled=True,
        )

        m.post(f"{ZAKEN_ROOT}zaakinformatieobjecten", status_code=500)

        response = self.app.get(self.case_detail_url, user=self.user)
        form = response.forms["document-upload"]
        form["title"] = "A title"
        form["file"] = Upload("upload.txt", b"data", "text/plain")
        form_response = form.submit()

        form_response_messages = list(form_response.context["messages"])

        self.assertEqual(
            form_response_messages[0].message,
            _(
                f"Een fout is opgetreden bij het uploaden van {self.uploaded_informatie_object['bestandsnaam']}"
            ),
        )
