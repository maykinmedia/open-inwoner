from django.test import override_settings
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
from open_inwoner.utils.test import ClearCachesMixin, paginated_response
from open_inwoner.utils.tests.playwright import (
    PlaywrightSyncLiveServerTestCase,
    multi_browser,
)


@requests_mock.Mocker()
@multi_browser()
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class CasesPlaywrightTests(ClearCachesMixin, PlaywrightSyncLiveServerTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.user = DigidUserFactory(bsn="900222086")
        # let's reuse the login storage_state
        self.user_login_state = self.get_user_bsn_login_state(self.user)

        # services
        self.zaak_service = ServiceFactory(api_root=ZAKEN_ROOT, api_type=APITypes.zrc)
        self.catalogi_service = ServiceFactory(
            api_root=CATALOGI_ROOT, api_type=APITypes.ztc
        )
        self.document_service = ServiceFactory(
            api_root=DOCUMENTEN_ROOT, api_type=APITypes.drc
        )
        # openzaak config
        self.config = OpenZaakConfig.get_solo()
        self.config.zaak_service = self.zaak_service
        self.config.catalogi_service = self.catalogi_service
        self.config.document_service = self.document_service
        self.config.document_max_confidentiality = (
            VertrouwelijkheidsAanduidingen.beperkt_openbaar
        )
        self.config.zaak_max_confidentiality = (
            VertrouwelijkheidsAanduidingen.beperkt_openbaar
        )
        self.config.save()

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
        self.status_finish = generate_oas_component(
            "zrc",
            "schemas/Status",
            url=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
            zaak=self.zaak["url"],
            statustype=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-744516671fe4",
            datumStatusGezet="2021-03-12",
            statustoelichting="",
        )
        self.status_type_finish = generate_oas_component(
            "ztc",
            "schemas/StatusType",
            url=self.status_finish["statustype"],
            zaaktype=self.zaaktype["url"],
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            omschrijving="Finish",
            omschrijvingGeneriek="some content",
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

        # enable upload
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

    def _setUpMocks(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        mock_service_oas_get(m, DOCUMENTEN_ROOT, "drc")

        self.matchers = []

        for resource in [
            self.zaak,
            self.result,
            self.zaaktype,
            # self.informatie_object_type,
            self.informatie_object,
            self.uploaded_informatie_object,
            # self.zaaktype_informatie_object_type,
            self.status_finish,
            self.status_type_finish,
        ]:
            self.matchers.append(m.get(resource["url"], json=resource))

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
        ]

    def test_cases(self, m):
        self._setUpMocks(m)

        context = self.browser.new_context(storage_state=self.user_login_state)

        page = context.new_page()
        page.goto(self.live_reverse("cases:open_cases"))

        # expected anchors
        menu_items = page.get_by_role(
            "complementary", name=_("Secundaire paginanavigatie")
        ).get_by_role("listitem")

        expect(menu_items.get_by_role("link", name=_("Open aanvragen"))).to_be_visible()
        expect(
            menu_items.get_by_role("link", name=_("Lopende aanvragen"))
        ).to_be_visible()
        expect(
            menu_items.get_by_role("link", name=_("Afgeronde aanvragen"))
        ).to_be_visible()

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

        # out-of-band anchor menu
        menu_items = page.get_by_role(
            "complementary", name=_("Secundaire paginanavigatie")
        ).get_by_role("listitem")

        expect(menu_items.get_by_role("link", name=_("Gegevens"))).to_be_visible()
        expect(menu_items.get_by_role("link", name=_("Status"))).to_be_visible()
        expect(menu_items.get_by_role("link", name=_("Documenten"))).to_be_visible()

        # check documents show
        documents = page.locator(".file-list").get_by_role("listitem")

        expect(documents).to_have_count(1)
        expect(documents).to_contain_text("uploaded_document_title")
        expect(documents).to_contain_text("(txt, 123 bytes)")
        expect(documents.get_by_role("link", name="Download")).to_be_visible()

        # check upload form and submit file
        upload_form = page.locator("#document-upload")
        expect(upload_form).to_be_visible()

        upload_form.get_by_label(_("Document selecteren")).set_input_files(
            files=[
                {
                    "name": "uploaded_test_file.txt",
                    "mimeType": "text/plain",
                    "buffer": self.uploaded_zaak_informatie_object_content,
                }
            ],
        )
        submit_button = upload_form.get_by_role("button", name=_("Document uploaden"))
        expect(submit_button).to_be_visible()

        title_input = upload_form.get_by_label(_("Titel bestand"))
        expect(title_input).to_be_visible()
        title_input.fill("uploaded document")

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

        # finally check if our mock matchers are accurate
        self.assertMockMatchersCalledAll(self.matchers)

    def assertMockMatchersCalledAll(self, matchers):
        def _match_str(m):
            return f"  {m._method.ljust(5, ' ')} {m._url}"

        missed = [m for m in matchers if not m.called]
        if not missed:
            return

        out = "\n".join(_match_str(m) for m in missed)
        self.fail(f"request mock matchers not called:\n{out}")
