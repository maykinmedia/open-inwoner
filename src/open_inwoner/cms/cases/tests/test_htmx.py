import json
from uuid import UUID

from django.test import override_settings, tag
from django.utils.translation import gettext as _

import requests_mock
from playwright.sync_api import expect
from zgw_consumers.api_models.constants import (
    RolOmschrijving,
    RolTypes,
    VertrouwelijkheidsAanduidingen,
)
from zgw_consumers.constants import APITypes
from zgw_consumers.test import generate_oas_component, mock_service_oas_get

from open_inwoner.accounts.tests.factories import DigidUserFactory
from open_inwoner.cms.tests import cms_tools
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.openklant.constants import Status
from open_inwoner.openklant.models import OpenKlantConfig
from open_inwoner.openklant.tests.data import (
    CONTACTMOMENTEN_ROOT,
    KLANTEN_ROOT,
    MockAPIData,
)
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.tests.factories import (
    ServiceFactory,
    ZaakTypeConfigFactory,
    ZaakTypeInformatieObjectTypeConfigFactory,
)
from open_inwoner.openzaak.tests.shared import (
    CATALOGI_ROOT,
    DOCUMENTEN_ROOT,
    ZAKEN_ROOT,
)
from open_inwoner.utils.test import (
    ClearCachesMixin,
    DisableRequestLogMixin,
    paginated_response,
)
from open_inwoner.utils.tests.helpers import AssertMockMatchersMixin
from open_inwoner.utils.tests.playwright import PlaywrightSyncLiveServerTestCase


@tag("e2e")
@requests_mock.Mocker()
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class CasesPlaywrightTests(
    AssertMockMatchersMixin,
    ClearCachesMixin,
    DisableRequestLogMixin,
    PlaywrightSyncLiveServerTestCase,
):
    def setUp(self) -> None:
        super().setUp()

        self.user = DigidUserFactory(bsn="900222086")
        self.user_login_state = self.get_user_bsn_login_state(self.user)

        # cookiebanner
        self.config = SiteConfiguration.get_solo()
        cms_tools.create_homepage()
        self.config.cookie_info_text = ""
        self.config.save()

        # services
        self.zaak_service = ServiceFactory(api_root=ZAKEN_ROOT, api_type=APITypes.zrc)
        self.catalogi_service = ServiceFactory(
            api_root=CATALOGI_ROOT, api_type=APITypes.ztc
        )
        self.document_service = ServiceFactory(
            api_root=DOCUMENTEN_ROOT, api_type=APITypes.drc
        )
        # openzaak config
        self.oz_config = OpenZaakConfig.get_solo()
        self.oz_config.zaak_service = self.zaak_service
        self.oz_config.catalogi_service = self.catalogi_service
        self.oz_config.document_service = self.document_service
        self.oz_config.document_max_confidentiality = (
            VertrouwelijkheidsAanduidingen.beperkt_openbaar
        )
        self.oz_config.zaak_max_confidentiality = (
            VertrouwelijkheidsAanduidingen.beperkt_openbaar
        )
        self.oz_config.save()

        # openklant config
        self.ok_config = OpenKlantConfig.get_solo()
        self.ok_config.register_contact_moment = True
        self.ok_config.register_bronorganisatie_rsin = "123456788"
        self.ok_config.register_type = "Melding"
        self.ok_config.register_employee_id = "FooVonBar"
        self.ok_config.klanten_service = ServiceFactory(
            api_root=KLANTEN_ROOT, api_type=APITypes.kc
        )
        self.ok_config.contactmomenten_service = ServiceFactory(
            api_root=CONTACTMOMENTEN_ROOT, api_type=APITypes.cmc
        )
        self.ok_config.save()

        self.zaak = generate_oas_component(
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
            resultaat=f"{ZAKEN_ROOT}resultaten/a44153aa-ad2c-6a07-be75-15add5113",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.zaaktype = generate_oas_component(
            "ztc",
            "schemas/ZaakType",
            uuid="0caa29cb-0167-426f-8dc1-88bebd7c8804",
            url=self.zaak["zaaktype"],
            identificatie="ZAAKTYPE-2020-0000000001",
            omschrijving="Coffee zaaktype",
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            indicatieInternOfExtern="extern",
        )
        #
        # statuses
        #
        self.status_new = generate_oas_component(
            "zrc",
            "schemas/Status",
            url=f"{ZAKEN_ROOT}statussen/3da81560-c7fc-476a-ad13-beu760sle929",
            zaak=self.zaak["url"],
            statustype=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-777yu878km09",
            datumStatusGezet="2021-01-12",
            statustoelichting="",
        )
        self.status_finish = generate_oas_component(
            "zrc",
            "schemas/Status",
            url=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
            zaak=self.zaak["url"],
            statustype=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-744516671fe4",
            datumStatusGezet="2021-03-12",
            statustoelichting="",
        )
        #
        # status types
        #
        self.status_type_new = generate_oas_component(
            "ztc",
            "schemas/StatusType",
            url=self.status_new["statustype"],
            zaaktype=self.zaaktype["url"],
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            omschrijving="Initial request",
            omschrijvingGeneriek="Nieuw",
            statustekst="",
            volgnummer=1,
            isEindstatus=False,
        )
        self.status_type_finish = generate_oas_component(
            "ztc",
            "schemas/StatusType",
            url=self.status_finish["statustype"],
            zaaktype=self.zaaktype["url"],
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            omschrijving="Finish",
            omschrijvingGeneriek="Afgehandeld",
            statustekst="",
            volgnummer=1,
            isEindstatus=True,
        )
        self.user_role = generate_oas_component(
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
        self.result = generate_oas_component(
            "zrc",
            "schemas/Resultaat",
            uuid="a44153aa-ad2c-6a07-be75-15add5113",
            url=self.zaak["resultaat"],
            resultaattype=f"{CATALOGI_ROOT}resultaattypen/b1a268dd-4322-47bb-a930-b83066b4a32c",
            zaak=self.zaak["url"],
            toelichting="resultaat toelichting",
        )
        self.zaak_informatie_object = generate_oas_component(
            "zrc",
            "schemas/ZaakInformatieObject",
            url=f"{ZAKEN_ROOT}zaakinformatieobjecten/e55153aa-ad2c-4a07-ae75-15add57d6",
            informatieobject=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812",
            zaak=self.zaak["url"],
        )
        self.informatie_object_type = generate_oas_component(
            "ztc",
            "schemas/InformatieObjectType",
            url=f"{CATALOGI_ROOT}informatieobjecttype/014c38fe-b010-4412-881c-3000032fb321",
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            omschrijving="Some content",
        )
        self.zaaktype_informatie_object_type = generate_oas_component(
            "ztc",
            "schemas/ZaakTypeInformatieObjectType",
            uuid="3fb03882-f6f9-4e0d-ad92-f810e24b9abb",
            url=f"{CATALOGI_ROOT}zaaktype-informatieobjecttypen/93250e6d-ef92-4474-acca-a6dbdcd61b7e",
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            zaaktype=self.zaaktype["url"],
            informatieobjecttype=self.informatie_object_type["url"],
            # volgnummer=1,
            richting="inkomend",
            statustype=self.status_type_finish,
        )
        self.informatie_object = generate_oas_component(
            "drc",
            "schemas/EnkelvoudigInformatieObject",
            uuid="014c38fe-b010-4412-881c-3000032fb812",
            url=self.zaak_informatie_object["informatieobject"],
            inhoud=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812/download",
            informatieobjecttype=self.informatie_object_type["url"],
            status="definitief",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            bestandsnaam="uploaded_document.txt",
            titel="uploaded_document_title.txt",
            bestandsomvang=123,
        )

        # for upload testing
        self.uploaded_zaak_informatie_object = generate_oas_component(
            "zrc",
            "schemas/ZaakInformatieObject",
            url=f"{ZAKEN_ROOT}zaakinformatieobjecten/48599f76-b524-48e8-be5a-6fc47288c9bf",
            informatieobject=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/48599f76-b524-48e8-be5a-6fc47288c9bf",
            zaak=self.zaak["url"],
        )
        self.uploaded_zaak_informatie_object_content = "test56789".encode("utf8")
        self.uploaded_informatie_object = generate_oas_component(
            "drc",
            "schemas/EnkelvoudigInformatieObject",
            uuid="48599f76-b524-48e8-be5a-6fc47288c9bf",
            url=self.uploaded_zaak_informatie_object["informatieobject"],
            inhoud=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/85079ba3-554a-450f-b963-2ce20b176c90/download",
            informatieobjecttype=self.informatie_object_type["url"],
            status="definitief",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            bestandsnaam="uploaded_test_file.txt",
            titel="uploaded_test_file.txt",
            bestandsomvang=len(self.uploaded_zaak_informatie_object_content),
        )
        self.klant = generate_oas_component(
            "kc",
            "schemas/Klant",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            bronorganisatie="123456789",
            voornaam="Foo",
            achternaam="Bar",
            emailadres="foo@example.com",
            telefoonnummer="0612345678",
        )
        self.contactmoment = generate_oas_component(
            "cmc",
            "schemas/ContactMoment",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-bbbbbbbbbbbb",
            url=f"{CONTACTMOMENTEN_ROOT}contactmoment/aaaaaaaa-aaaa-aaaa-aaaa-bbbbbbbbbbbb",
            status=Status.nieuw,
            antwoord="",
            text="hey!\n\nwaddup?",
        )
        self.klant_contactmoment = generate_oas_component(
            "cmc",
            "schemas/KlantContactMoment",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc",
            url=f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten/aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc",
            klant=self.klant["url"],
            contactmoment=self.contactmoment["url"],
        )

        # enable upload and contact form
        zaak_type_config = ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
            contact_form_enabled=True,
        )
        ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url=self.informatie_object["url"],
            zaaktype_uuids=[self.zaaktype["uuid"]],
            document_upload_enabled=True,
        )

    def _setUpMocks(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        mock_service_oas_get(m, DOCUMENTEN_ROOT, "drc")
        MockAPIData.setUpOASMocks(m)

        self.matchers = []

        for resource in [
            self.zaak,
            self.result,
            self.zaaktype,
            self.status_type_new,
            self.status_type_finish,
        ]:
            m.get(resource["url"], json=resource)

        for resource in [
            self.zaak,
            self.result,
            self.zaaktype,
            self.informatie_object,
            self.uploaded_informatie_object,
            self.status_finish,
            self.status_type_finish,
        ]:
            self.matchers.append(m.get(resource["url"], json=resource))

        # mock `fetch_status_types_no_cache`
        m.get(
            f"{CATALOGI_ROOT}statustypen?zaaktype={self.zaak['zaaktype']}",
            json=paginated_response([self.status_type_new, self.status_type_finish]),
        )

        self.matchers += [
            m.get(
                f"{ZAKEN_ROOT}zaken?rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn={self.user.bsn}&maximaleVertrouwelijkheidaanduiding=beperkt_openbaar",
                json=paginated_response([self.zaak]),
            ),
            m.get(
                f"{ZAKEN_ROOT}zaakinformatieobjecten?zaak={self.zaak['url']}",
                [
                    {
                        "json": [
                            self.zaak_informatie_object,
                        ]
                    },
                    # after upload
                    {
                        "json": [
                            self.zaak_informatie_object,
                            self.uploaded_zaak_informatie_object,
                        ]
                    },
                ],
            ),
            m.get(
                f"{ZAKEN_ROOT}statussen?zaak={self.zaak['url']}",
                json=paginated_response([self.status_finish]),
            ),
            m.get(
                f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}",
                json=paginated_response([self.user_role]),
            ),
            m.get(
                f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}&omschrijvingGeneriek={RolOmschrijving.initiator}",
                # Taiga #961 this is not an accurate OpenZaak response as it has a 'behandelaar' even when we filter on 'initiator'
                # but eSuite doesn't filter the response in the API, so we use filtering in Python to remove the not-initiator
                json=paginated_response([self.user_role]),
            ),
            # upload
            m.post(
                f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten",
                status_code=201,
                json=self.uploaded_informatie_object,
            ),
            m.post(
                f"{ZAKEN_ROOT}zaakinformatieobjecten",
                status_code=201,
                json=self.uploaded_zaak_informatie_object,
            ),
            m.get(
                self.uploaded_informatie_object["inhoud"],
                content=self.uploaded_zaak_informatie_object_content,
            ),
            m.get(
                f"{KLANTEN_ROOT}klanten?subjectNatuurlijkPersoon__inpBsn=900222086",
                json=paginated_response([self.klant]),
            ),
            m.post(
                f"{CONTACTMOMENTEN_ROOT}contactmomenten",
                json=self.contactmoment,
                status_code=201,
            ),
            m.post(
                f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten",
                json=self.klant_contactmoment,
                status_code=201,
            ),
        ]

    def test_cases(self, m):
        self._setUpMocks(m)

        context = self.browser.new_context(storage_state=self.user_login_state)

        page = context.new_page()
        page.goto(self.live_reverse("cases:index"))

        # case title
        case_title = page.get_by_role("link", name=self.zaaktype["omschrijving"])
        expect(case_title).to_be_visible()

        # go to case-detail page
        case_title.click()
        page.wait_for_url(
            self.live_reverse(
                "cases:case_detail", kwargs={"object_id": self.zaak["uuid"]}, star=True
            )
        )

        # check case is visible
        expect(page.get_by_text(self.zaak["identificatie"])).to_be_visible()

        # check documents show
        documents = page.locator(".file-list").get_by_role("listitem")

        expect(documents).to_have_count(1)
        expect(documents).to_contain_text("uploaded_document_title")
        expect(documents).to_contain_text("(txt, 123 bytes)")
        expect(documents.get_by_role("link", name="Download")).to_be_visible()

        # check upload form and submit file
        upload_form = page.locator("#document-upload")
        expect(upload_form).to_be_visible()

        file_input = upload_form.get_by_label(
            _("Sleep of selecteer bestanden"), exact=True
        )
        file_input.set_input_files(
            files=[
                {
                    "name": "uploaded_test_file.txt",
                    "mimeType": "text/plain",
                    "buffer": self.uploaded_zaak_informatie_object_content,
                }
            ],
        )
        submit_button = upload_form.get_by_role("button", name=_("Upload documenten"))
        expect(submit_button).to_be_visible()

        submit_button.click()

        # check for new file
        expect(documents).to_have_count(2)
        uploaded_doc = documents.nth(1)
        expect(uploaded_doc).to_contain_text("uploaded_test_file")
        expect(uploaded_doc).to_contain_text("(txt, 9 bytes)")

        download_link = uploaded_doc.get_by_role("link", name="Download")
        expect(download_link).to_be_visible()

        with page.expect_download() as download_info:
            download_link.click()
        download = download_info.value

        self.assertEqual(download.suggested_filename, "uploaded_test_file.txt")
        with open(download.path(), "rb") as f:
            self.assertEqual(f.read(), self.uploaded_zaak_informatie_object_content)

        # contact form
        contact_form = page.locator("#contact-form")
        expect(contact_form).to_be_visible()

        question_text_area = page.get_by_role("textbox", name=_("Vraag"))
        expect(question_text_area).to_be_visible()

        question_text_area.fill("a question")
        contact_submit_button = contact_form.get_by_role(
            "button", name=_("Vraag versturen")
        )
        expect(contact_submit_button).to_be_visible()

        contact_submit_button.click()

        notification = page.locator(".notification__content")
        expect(notification).to_be_visible()
        expect(notification.get_by_text(_("Vraag verstuurd!"))).to_be_visible()

        # finally check if our mock matchers are accurate
        self.assertMockMatchersCalled(self.matchers)

    def test_multiple_file_upload(self, m):
        self._setUpMocks(m)

        # Keep track of uploaded files (schemas/EnkelvoudigInformatieObject array)
        # This list is updated by mocks after uploading the files.
        uploads = []

        # Document list mock.
        def mock_list(request, context):
            """
            Mock GET "zaakinformatieobjecten" endpoint (schemas/ZaakInformatieObject array).
            Creates schemas/ZaakInformatieObject dict for each item in uploads.
            """
            items = [
                generate_oas_component(
                    "zrc",
                    "schemas/ZaakInformatieObject",
                    url=f"{ZAKEN_ROOT}zaakinformatieobjecten/e55153aa-ad2c-4a07-ae75-15add57d6",
                    informatieobject=upload["url"],
                    zaak=self.zaak["url"],
                )
                for upload in uploads
            ]
            return json.dumps(items)

        m.get(
            f"{ZAKEN_ROOT}zaakinformatieobjecten?zaak={self.zaak['url']}",
            text=mock_list,
        ),

        # Upload mock.
        def mock_upload(request, context):
            """
            Mock POST "enkelvoudiginformatieobjecten" endpoint (schemas/EnkelvoudigInformatieObject).
            Creates schemas/EnkelvoudigInformatieObject dict and mock for its url.
            appends created item to `uploads`.
            """
            request_body = json.loads(request.body)
            file_name = request_body["titel"]

            # Create a UUID based on a seed derived from the file name.
            # This makes sure the two test cases have unique entries.
            seed = file_name.ljust(16, "0").encode("utf-8")
            uuid = UUID(bytes=seed)

            uploaded_informatie_object = generate_oas_component(
                "drc",
                "schemas/EnkelvoudigInformatieObject",
                uuid=str(uuid),
                url=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/{uuid}",
                inhoud=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/85079ba3-554a-450f-b963-2ce20b176c90/download",
                informatieobjecttype=self.informatie_object_type["url"],
                status="definitief",
                vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
                bestandsnaam=file_name,
                titel=file_name,
                bestandsomvang=request_body["bestandsomvang"],
            )
            m.get(uploaded_informatie_object["url"], json=uploaded_informatie_object)
            uploads.append(uploaded_informatie_object)
            return json.dumps(uploaded_informatie_object)

        m.post(
            f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten",
            status_code=201,
            text=mock_upload,
        ),

        # Setup.
        context = self.browser.new_context(storage_state=self.user_login_state)
        page = context.new_page()
        page.goto(
            self.live_reverse(
                "cases:case_detail", kwargs={"object_id": self.zaak["uuid"]}
            )
        )

        upload_form = page.locator("#document-upload")
        file_input = upload_form.get_by_label("Sleep of selecteer bestanden")
        submit_button = upload_form.get_by_role("button", name=_("Upload documenten"))
        notification_list = page.get_by_role("alert").get_by_role("list")
        notification_list_items = notification_list.get_by_role("listitem")
        file_list = page.get_by_role("list").last
        file_list_items = file_list.get_by_role("listitem")

        # Check that the initial state does not have any uploaded documents.
        expect(notification_list_items).to_have_count(0)
        expect(file_list_items).to_have_count(0)

        # Upload some files.
        file_input.set_input_files(
            files=[
                {
                    "name": "document_1.txt",
                    "mimeType": "text/plain",
                    "buffer": "test12345".encode("utf8"),
                },
                {
                    "name": "document_two.pdf",
                    "mimeType": "application/pdf",
                    "buffer": "test67890".encode("utf8"),
                },
            ],
        )
        submit_button.click()
        page.wait_for_url(
            self.live_reverse(
                "cases:case_detail", kwargs={"object_id": self.zaak["uuid"]}
            )
        )

        # Check that the case does now have two uploaded documents.
        expect(notification_list_items).to_have_count(2)
        expect(notification_list_items.first).to_contain_text("document_1.txt")
        expect(notification_list_items.last).to_contain_text("document_two.pdf")
        expect(file_list_items).to_have_count(2)
        expect(file_list_items.first).to_contain_text("document_1")
        expect(file_list_items.first).to_contain_text("(txt, 9 bytes)")
        expect(file_list_items.last).to_contain_text("document_two")
        expect(file_list_items.last).to_contain_text("(pdf, 9 bytes)")
