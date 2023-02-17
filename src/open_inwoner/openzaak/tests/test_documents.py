from datetime import date
from io import BytesIO

from django.contrib.auth.models import AnonymousUser
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import requests_mock
from django_webtest import WebTest
from privates.test import temp_private_root
from timeline_logger.models import TimelineLog
from zgw_consumers.api_models.constants import (
    RolOmschrijving,
    RolTypes,
    VertrouwelijkheidsAanduidingen,
)
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test import generate_oas_component, mock_service_oas_get

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.accounts.views.cases import SimpleFile
from open_inwoner.utils.test import ClearCachesMixin, paginated_response

from ..cases import connect_case_with_document
from ..documents import download_document, upload_document
from ..models import OpenZaakConfig
from .factories import (
    CertificateFactory,
    ServiceFactory,
    ZaakTypeConfigFactory,
    ZaakTypeInformatieObjectTypeConfigFactory,
)
from .shared import CATALOGI_ROOT, DOCUMENTEN_ROOT, ZAKEN_ROOT


def get_temporary_text_file():
    io = BytesIO(b"some content")
    text_file = InMemoryUploadedFile(
        io, None, "foo.txt", "plain/text", len(io.getvalue()), None
    )
    text_file.seek(0)
    return text_file


@temp_private_root()
@requests_mock.Mocker()
class TestDocumentDownloadUpload(ClearCachesMixin, WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = UserFactory(
            login_type=LoginTypeChoices.digid, bsn="900222086", email="johm@smith.nl"
        )
        cls.config = OpenZaakConfig.get_solo()
        cls.zaak_service = ServiceFactory(api_root=ZAKEN_ROOT, api_type=APITypes.zrc)
        cls.config.zaak_service = cls.zaak_service
        cls.catalogi_service = ServiceFactory(
            api_root=CATALOGI_ROOT, api_type=APITypes.ztc
        )
        cls.config.catalogi_service = cls.catalogi_service
        cls.document_service = ServiceFactory(
            api_root=DOCUMENTEN_ROOT, api_type=APITypes.drc
        )
        cls.config.document_service = cls.document_service
        cls.config.document_max_confidentiality = (
            VertrouwelijkheidsAanduidingen.beperkt_openbaar
        )
        cls.config.zaak_max_confidentiality = (
            VertrouwelijkheidsAanduidingen.beperkt_openbaar
        )
        cls.config.save()

        cls.zaak = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            uuid="d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            url=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/0caa29cb-0167-426f-8dc1-88bebd7c8804",
            identificatie="ZAAK-2022-0000000024",
            omschrijving="Zaak naar aanleiding van ingezonden formulier",
            startdatum="2022-01-02",
            einddatum=None,
            status=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            bronorganisatie="123456782",
        )
        cls.zaaktype = generate_oas_component(
            "ztc",
            "schemas/ZaakType",
            url=cls.zaak["zaaktype"],
            uuid="0caa29cb-0167-426f-8dc1-88bebd7c8804",
            omschrijving="Coffee zaaktype",
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            # openbaar and extern
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            indicatieInternOfExtern="extern",
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
        cls.not_our_user_role = generate_oas_component(
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
        cls.informatie_object_content = "my document content".encode("utf8")
        cls.informatie_object = generate_oas_component(
            "drc",
            "schemas/EnkelvoudigInformatieObject",
            uuid="014c38fe-b010-4412-881c-3000032fb812",
            url=cls.zaak_informatie_object["informatieobject"],
            inhoud=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812/download",
            informatieobjecttype=f"{CATALOGI_ROOT}informatieobjecttype/014c38fe-b010-4412-881c-3000032fb321",
            status="definitief",
            indicatieGebruiksrecht=False,
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            formaat="text/plain",
            bestandsnaam="my_document.txt",
            bestandsomvang=len(cls.informatie_object_content),
            bronorganisatie="1233456782",
            creatiedatum=date.today().strftime("%Y-%m-%d"),
            titel="",
            auteur="Open Inwoner Platform",
        )
        cls.informatie_object_file = SimpleFile(
            name="my_document.txt",
            size=len(cls.informatie_object_content),
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

    def _setUpAccessMocks(self, m):
        # the minimal mocks needed to be able to access the information object
        self._setUpOASMocks(m)
        m.get(self.zaak["url"], json=self.zaak)
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}",
            json=paginated_response([self.user_role, self.not_our_user_role]),
        )
        m.get(self.zaaktype["url"], json=self.zaaktype)
        m.get(
            f"{ZAKEN_ROOT}zaakinformatieobjecten?zaak={self.zaak['url']}&informatieobject={self.informatie_object['url']}",
            # note the real API doesn't return a paginated_response here
            json=[self.zaak_informatie_object],
        )

    def _setUpMocks(self, m):
        self._setUpAccessMocks(m)
        m.get(self.informatie_object["url"], json=self.informatie_object)
        m.get(self.informatie_object["inhoud"], content=self.informatie_object_content)
        m.post(
            f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten",
            status_code=201,
            json=self.informatie_object,
        )
        m.post(
            f"{ZAKEN_ROOT}zaakinformatieobjecten",
            status_code=201,
            json=self.zaak_informatie_object,
        )

    def test_document_content_is_retrieved_when_user_logged_in_via_digid(self, m):
        self._setUpMocks(m)
        url = reverse(
            "accounts:case_document_download",
            kwargs={
                "object_id": self.zaak["uuid"],
                "info_id": self.informatie_object["uuid"],
            },
        )
        response = self.app.get(url, user=self.user)

        self.assertEqual(response.body, self.informatie_object_content)
        self.assertIn("Content-Disposition", response.headers)
        self.assertEqual(
            response.headers["Content-Disposition"],
            f'attachment; filename="my_document.txt"',
        )
        self.assertIn("Content-Type", response.headers)
        self.assertEqual(response.headers["Content-Type"], "text/plain")
        self.assertIn("Content-Length", response.headers)
        self.assertEqual(
            response.headers["Content-Length"], str(len(self.informatie_object_content))
        )

    def test_document_retrieval_logs_case_identification_and_file(self, m):
        self._setUpMocks(m)
        url = reverse(
            "accounts:case_document_download",
            kwargs={
                "object_id": self.zaak["uuid"],
                "info_id": self.informatie_object["uuid"],
            },
        )
        self.app.get(url, user=self.user)

        log = TimelineLog.objects.last()
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.content_object, self.user)
        expected = _("Document van zaak gedownload {case}: {filename}").format(
            case=self.zaak["identificatie"],
            filename=self.informatie_object_file.name,
        )
        self.assertEqual(log.extra_data["message"], expected)

    def test_document_content_with_bad_status_is_http_403(self, m):
        self._setUpAccessMocks(m)

        info_object = generate_oas_component(
            "drc",
            "schemas/EnkelvoudigInformatieObject",
            uuid="014c38fe-b010-4412-881c-3000032fb812",
            url=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812",
            informatieobjecttype=f"{CATALOGI_ROOT}informatieobjecttype/014c38fe-b010-4412-881c-3000032fb321",
            # bad status
            status="archief",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        m.get(info_object["url"], json=info_object)
        url = reverse(
            "accounts:case_document_download",
            kwargs={
                "object_id": self.zaak["uuid"],
                "info_id": info_object["uuid"],
            },
        )
        self.app.get(url, user=self.user, status=403)

    def test_document_content_with_bad_confidentiality_is_http_403(self, m):
        self._setUpAccessMocks(m)

        info_object = generate_oas_component(
            "drc",
            "schemas/EnkelvoudigInformatieObject",
            uuid="014c38fe-b010-4412-881c-3000032fb812",
            url=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812",
            informatieobjecttype=f"{CATALOGI_ROOT}informatieobjecttype/014c38fe-b010-4412-881c-3000032fb321",
            status="definitief",
            # bad confidentiality
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.geheim,
        )
        m.get(info_object["url"], json=info_object)
        url = reverse(
            "accounts:case_document_download",
            kwargs={
                "object_id": self.zaak["uuid"],
                "info_id": info_object["uuid"],
            },
        )
        self.app.get(url, user=self.user, status=403)

    def test_response_is_http_403_when_not_logged_in_via_digid(self, m):
        self._setUpMocks(m)
        user = UserFactory(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.default,
        )
        self.app.get(self.informatie_object_file.url, user=user, status=403)

    def test_anonymous_user_has_no_access_to_download_page(self, m):
        self._setUpMocks(m)
        user = AnonymousUser()
        self.app.get(self.informatie_object_file.url, user=user, status=403)

    def test_no_data_is_retrieved_when_case_object_http_404(self, m):
        self._setUpOASMocks(m)
        m.get(self.zaak["url"], status_code=404)

        self.app.get(self.informatie_object_file.url, user=self.user, status=404)

    def test_no_data_is_retrieved_when_no_related_roles_are_found_for_user_bsn(self, m):
        self._setUpOASMocks(m)
        m.get(self.zaak["url"], json=self.zaak)
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}",
            # no roles for our user found
            json=paginated_response([self.not_our_user_role]),
        )
        self.app.get(self.informatie_object_file.url, user=self.user, status=403)

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

    def test_no_data_is_retrieved_when_no_matching_case_info_object_is_found(self, m):
        self._setUpOASMocks(m)
        m.get(self.zaak["url"], json=self.zaak)
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}",
            json=paginated_response([self.user_role, self.not_our_user_role]),
        )
        m.get(self.zaaktype["url"], json=self.zaaktype)
        m.get(self.informatie_object["url"], json=self.informatie_object)
        m.get(
            f"{ZAKEN_ROOT}zaakinformatieobjecten?zaak={self.zaak['url']}&informatieobject={self.informatie_object['url']}",
            # no case info objects found
            json=[],
        )
        self.app.get(self.informatie_object_file.url, user=self.user, status=403)

    def test_no_data_is_retrieved_when_info_object_http_404(self, m):
        self._setUpAccessMocks(m)
        m.get(self.informatie_object["url"], status_code=404)

        self.app.get(self.informatie_object_file.url, user=self.user, status=404)

    def test_no_data_is_retrieved_when_info_object_http_500(self, m):
        self._setUpAccessMocks(m)
        m.get(self.informatie_object["url"], status_code=500)

        self.app.get(self.informatie_object_file.url, user=self.user, status=404)

    def test_no_data_is_retrieved_when_document_download_data_http_404(self, m):
        self._setUpAccessMocks(m)
        m.get(self.informatie_object["url"], json=self.informatie_object)
        m.get(self.informatie_object["inhoud"], status_code=404)

        self.app.get(self.informatie_object_file.url, user=self.user, status=404)

    def test_no_data_is_retrieved_when_document_download_data_http_500(self, m):
        self._setUpAccessMocks(m)
        m.get(self.informatie_object["url"], json=self.informatie_object)
        m.get(self.informatie_object["inhoud"], status_code=500)

        self.app.get(self.informatie_object_file.url, user=self.user, status=404)

    def test_document_download_request_uses_service_credentials(self, m):
        server = CertificateFactory(label="server", cert_only=True)
        client = CertificateFactory(label="client", key_pair=True)

        self.document_service.server_certificate = server
        self.document_service.client_certificate = client

        self.document_service.client_id = "abc123"
        self.document_service.secret = "secret"
        self.document_service.auth_type = AuthTypes.zgw
        self.document_service.save()

        m.get(self.informatie_object["inhoud"], content=self.informatie_object_content)

        download_document(self.informatie_object["inhoud"])

        req = m.request_history[0]
        self.assertEqual(req.verify, server.public_certificate.path)
        self.assertEqual(req.cert[0], client.public_certificate.path)
        self.assertEqual(req.cert[1], client.private_key.path)
        self.assertIn("Bearer ", req.headers["Authorization"])

    def test_document_is_uploaded(self, m):
        self._setUpMocks(m)

        zaak_type_config = ZaakTypeConfigFactory(
            identificatie=self.zaaktype["identificatie"]
        )
        zaak_type_iotc = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url=self.informatie_object["url"],
            zaaktype_uuids=[self.zaaktype["uuid"]],
            document_upload_enabled=True,
        )
        file = get_temporary_text_file()
        title = "my_document"

        created_document = upload_document(
            self.user, file, title, zaak_type_iotc.id, self.zaak["bronorganisatie"]
        )

        self.assertEqual(created_document, self.informatie_object)

    def test_document_response_is_none_when_http_404(self, m):
        self._setUpMocks(m)

        zaak_type_config = ZaakTypeConfigFactory(
            identificatie=self.zaaktype["identificatie"]
        )
        zaak_type_iotc = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url=self.informatie_object["url"],
            zaaktype_uuids=[self.zaaktype["uuid"]],
            document_upload_enabled=True,
        )
        file = get_temporary_text_file()
        title = "my_document"

        m.post(f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten", status_code=404)
        created_document = upload_document(
            self.user, file, title, zaak_type_iotc.id, self.zaak["bronorganisatie"]
        )

        self.assertIsNone(created_document)

    def test_document_response_is_none_when_http_500(self, m):
        self._setUpMocks(m)

        zaak_type_config = ZaakTypeConfigFactory(
            identificatie=self.zaaktype["identificatie"]
        )
        zaak_type_iotc = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url=self.informatie_object["url"],
            zaaktype_uuids=[self.zaaktype["uuid"]],
            document_upload_enabled=True,
        )
        file = get_temporary_text_file()
        title = "my_document"

        m.post(f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten", status_code=500)
        created_document = upload_document(
            self.user, file, title, zaak_type_iotc.id, self.zaak["bronorganisatie"]
        )

        self.assertIsNone(created_document)

    def test_document_response_is_none_when_no_client_is_configured(self, m):
        self._setUpMocks(m)

        zaak_type_config = ZaakTypeConfigFactory(
            identificatie=self.zaaktype["identificatie"]
        )
        zaak_type_iotc = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url=self.informatie_object["url"],
            zaaktype_uuids=[self.zaaktype["uuid"]],
            document_upload_enabled=True,
        )
        self.config.document_service = None
        self.config.save()

        file = get_temporary_text_file()
        title = "my_document"

        created_document = upload_document(
            self.user, file, title, zaak_type_iotc.id, self.zaak["bronorganisatie"]
        )

        self.assertIsNone(created_document)

    def test_document_case_relationship_is_created(self, m):
        self._setUpMocks(m)

        created_relationship = connect_case_with_document(
            self.zaak["url"], self.informatie_object["url"]
        )

        self.assertEqual(created_relationship, self.zaak_informatie_object)

    def test_document_case_relationship_is_not_created_when_http_400(self, m):
        self._setUpMocks(m)

        m.post(
            f"{ZAKEN_ROOT}zaakinformatieobjecten",
            status_code=400,
        )
        created_relationship = connect_case_with_document(
            self.zaak["url"], self.informatie_object["url"]
        )

        self.assertIsNone(created_relationship)

    def test_document_case_relationship_is_not_created_when_http_500(self, m):
        self._setUpMocks(m)

        m.post(
            f"{ZAKEN_ROOT}zaakinformatieobjecten",
            status_code=500,
        )
        created_relationship = connect_case_with_document(
            self.zaak["url"], self.informatie_object["url"]
        )

        self.assertIsNone(created_relationship)

    def test_document_case_relationship_is_not_created_when_no_client_is_configured(
        self, m
    ):
        self._setUpMocks(m)

        self.config.zaak_service = None
        self.config.save()

        created_relationship = connect_case_with_document(
            self.zaak["url"], self.informatie_object["url"]
        )

        self.assertIsNone(created_relationship)
