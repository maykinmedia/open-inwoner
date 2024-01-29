from django.conf import settings
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils.translation import gettext as _

import requests_mock
from django_webtest import WebTest
from zgw_consumers.api_models.constants import (
    RolOmschrijving,
    RolTypes,
    VertrouwelijkheidsAanduidingen,
)
from zgw_consumers.constants import APITypes
from zgw_consumers.test import generate_oas_component, mock_service_oas_get

from open_inwoner.accounts.tests.factories import (
    DigidUserFactory,
    eHerkenningUserFactory,
)
from open_inwoner.openklant.constants import Status
from open_inwoner.openklant.models import OpenKlantConfig
from open_inwoner.openklant.tests.data import (
    CONTACTMOMENTEN_ROOT,
    KLANTEN_ROOT,
    MockAPIData,
)
from open_inwoner.openzaak.models import CatalogusConfig, OpenZaakConfig
from open_inwoner.openzaak.tests.factories import ServiceFactory, ZaakTypeConfigFactory
from open_inwoner.openzaak.tests.helpers import generate_oas_component_cached
from open_inwoner.openzaak.tests.shared import (
    CATALOGI_ROOT,
    DOCUMENTEN_ROOT,
    ZAKEN_ROOT,
)
from open_inwoner.utils.test import ClearCachesMixin, paginated_response
from open_inwoner.utils.tests.helpers import AssertMockMatchersMixin

PATCHED_MIDDLEWARE = [
    m
    for m in settings.MIDDLEWARE
    if m != "open_inwoner.kvk.middleware.KvKLoginMiddleware"
]


@requests_mock.Mocker()
@override_settings(
    ROOT_URLCONF="open_inwoner.cms.tests.urls", MIDDLEWARE=PATCHED_MIDDLEWARE
)
class CasesContactFormTestCase(AssertMockMatchersMixin, ClearCachesMixin, WebTest):
    def setUp(self):
        super().setUp()

        self.user = DigidUserFactory(bsn="900222086")

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

        self.zaak = generate_oas_component_cached(
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
        self.user_role = generate_oas_component_cached(
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
        self.eherkenning_user_role = generate_oas_component_cached(
            "zrc",
            "schemas/Rol",
            url=f"{ZAKEN_ROOT}rollen/3ff7686f-db35-4181-8e48-57521220f887",
            omschrijvingGeneriek=RolOmschrijving.initiator,
            betrokkeneType=RolTypes.niet_natuurlijk_persoon,
            betrokkeneIdentificatie={
                "innNnpId": "000000000",
                "voornamen": "Foo Bar",
                "voorvoegselGeslachtsnaam": "van der",
                "geslachtsnaam": "Bazz",
            },
        )
        self.eherkenning_user_role_kvk = generate_oas_component_cached(
            "zrc",
            "schemas/Rol",
            url=f"{ZAKEN_ROOT}rollen/5885531e-9b7f-46af-947e-f2278a2e72a8",
            omschrijvingGeneriek=RolOmschrijving.initiator,
            betrokkeneType=RolTypes.niet_natuurlijk_persoon,
            betrokkeneIdentificatie={
                "innNnpId": "12345678",
                "voornamen": "Foo Bar",
                "voorvoegselGeslachtsnaam": "van der",
                "geslachtsnaam": "Bazz",
            },
        )
        self.zaaktype = generate_oas_component_cached(
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
        self.status_new = generate_oas_component_cached(
            "zrc",
            "schemas/Status",
            url=f"{ZAKEN_ROOT}statussen/3da81560-c7fc-476a-ad13-beu760sle929",
            zaak=self.zaak["url"],
            statustype=f"{CATALOGI_ROOT}statustypen/t302de91-68b5-4bb2-9f65-fdd3083bace9",
            datumStatusGezet="2021-01-12",
            statustoelichting="",
        )
        self.status_finish = generate_oas_component_cached(
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
        self.status_type_new = generate_oas_component_cached(
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
        # no associated status (for testing `add_second_status_preview`)
        self.status_type_in_behandeling = generate_oas_component_cached(
            "ztc",
            "schemas/StatusType",
            url=f"{CATALOGI_ROOT}statustypen/167cb935-ac8a-428e-8cca-5abda0da47c7",
            zaaktype=self.zaaktype["url"],
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            omschrijving="In behandeling",
            omschrijvingGeneriek="some content",
            statustekst="",
            volgnummer=3,
            isEindstatus=False,
        )
        self.status_type_finish = generate_oas_component_cached(
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
        self.result = generate_oas_component_cached(
            "zrc",
            "schemas/Resultaat",
            uuid="a44153aa-ad2c-6a07-be75-15add5113",
            url=self.zaak["resultaat"],
            resultaattype=f"{CATALOGI_ROOT}resultaattypen/b1a268dd-4322-47bb-a930-b83066b4a32c",
            zaak=self.zaak["url"],
            toelichting="resultaat toelichting",
        )
        self.klant = generate_oas_component_cached(
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

        # contact form
        self.zaak_type_config = ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
            contact_form_enabled=True,
            contact_subject_code="afdeling-x",
        )

        self.case_detail_url = reverse(
            "cases:case_detail_content", kwargs={"object_id": self.zaak["uuid"]}
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
            self.status_finish,
            self.status_type_finish,
            self.status_type_new,
            self.status_type_in_behandeling,
        ]:
            self.matchers.append(m.get(resource["url"], json=resource))

        # mock `fetch_status_types_no_cache`
        m.get(
            f"{CATALOGI_ROOT}statustypen?zaaktype={self.zaak['zaaktype']}",
            json=paginated_response([self.status_type_new, self.status_type_finish]),
        )

        self.matchers += [
            m.get(
                f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}",
                json=paginated_response(
                    [
                        self.user_role,
                        self.eherkenning_user_role,
                        self.eherkenning_user_role_kvk,
                    ]
                ),
            ),
            m.get(
                f"{ZAKEN_ROOT}zaakinformatieobjecten?zaak={self.zaak['url']}",
                [{"json": []}],
            ),
            m.get(
                f"{ZAKEN_ROOT}statussen?zaak={self.zaak['url']}",
                json=paginated_response([self.status_finish]),
            ),
            m.get(
                f"{KLANTEN_ROOT}klanten?subjectNatuurlijkPersoon__inpBsn=900222086",
                json=paginated_response([self.klant]),
            ),
        ]

    def _setUpExtraMocks(self, m):
        self.contactmoment = generate_oas_component_cached(
            "cmc",
            "schemas/ContactMoment",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-bbbbbbbbbbbb",
            url=f"{CONTACTMOMENTEN_ROOT}contactmoment/aaaaaaaa-aaaa-aaaa-aaaa-bbbbbbbbbbbb",
            status=Status.nieuw,
            antwoord="",
            text="hey!\n\nwaddup?",
        )
        self.klant_contactmoment = generate_oas_component_cached(
            "cmc",
            "schemas/KlantContactMoment",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc",
            url=f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten/aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc",
            klant=self.klant["url"],
            contactmoment=self.contactmoment["url"],
        )
        self.matcher_create_contactmoment = m.post(
            f"{CONTACTMOMENTEN_ROOT}contactmomenten",
            json=self.contactmoment,
            status_code=201,
        )
        self.matcher_create_klantcontactmoment = m.post(
            f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten",
            json=self.klant_contactmoment,
            status_code=201,
        )
        self.extra_matchers = [
            self.matcher_create_contactmoment,
            self.matcher_create_klantcontactmoment,
        ]

    def test_form_is_shown_if_open_klant_api_configured(self, m):
        self._setUpMocks(m)

        self.assertTrue(self.ok_config.has_api_configuration())

        response = self.app.get(self.case_detail_url, user=self.user)
        contact_form = response.pyquery("#contact-form")

        self.assertTrue(response.context["case"]["contact_form_enabled"])
        self.assertTrue(contact_form)

    def test_form_is_shown_if_open_klant_email_configured(self, m):
        self._setUpMocks(m)

        self.ok_config.register_email = "example@example.com"
        self.ok_config.register_contact_moment = False
        self.ok_config.save()

        self.assertFalse(self.ok_config.has_api_configuration())
        self.assertTrue(self.ok_config.has_register())

        response = self.app.get(self.case_detail_url, user=self.user)
        contact_form = response.pyquery("#contact-form")

        self.assertTrue(response.context["case"]["contact_form_enabled"])
        self.assertTrue(contact_form)

    def test_form_is_shown_if_open_klant_email_and_api_configured(self, m):
        self._setUpMocks(m)

        self.ok_config.register_email = "example@example.com"
        self.ok_config.save()

        self.assertTrue(self.ok_config.has_api_configuration())
        self.assertTrue(self.ok_config.has_register())

        response = self.app.get(self.case_detail_url, user=self.user)
        contact_form = response.pyquery("#contact-form")

        self.assertTrue(response.context["case"]["contact_form_enabled"])
        self.assertTrue(contact_form)

    def test_no_form_shown_if_open_klant_not_configured(self, m):
        self._setUpMocks(m)

        # reset
        self.ok_config.klanten_service = None
        self.ok_config.contactmomenten_service = None
        self.ok_config.register_email = ""
        self.ok_config.register_contact_moment = False
        self.ok_config.register_bronorganisatie_rsin = ""
        self.ok_config.register_type = ""
        self.ok_config.register_employee_id = ""
        self.ok_config.save()
        self.assertFalse(self.ok_config.has_api_configuration())

        response = self.app.get(self.case_detail_url, user=self.user)
        contact_form = response.pyquery("#contact-form")

        self.assertFalse(response.context["case"]["contact_form_enabled"])
        self.assertFalse(contact_form)

    def test_no_form_shown_if_contact_form_disabled(self, m):
        self._setUpMocks(m)

        CatalogusConfig.objects.all().delete()
        self.zaak_type_config.delete()
        self.zaak_type_config = ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
            contact_form_enabled=False,
        )

        response = self.app.get(self.case_detail_url, user=self.user)
        contact_form = response.pyquery("#contact-form")

        self.assertFalse(response.context["case"]["contact_form_enabled"])
        self.assertFalse(contact_form)

    def test_form_success_with_api(self, m):
        self._setUpMocks(m)
        self._setUpExtraMocks(m)

        response = self.app.get(self.case_detail_url, user=self.user)
        form = response.forms["contact-form"]
        form.action = reverse(
            "cases:case_detail_contact_form", kwargs={"object_id": self.zaak["uuid"]}
        )
        form["question"] = "Sample text"
        response = form.submit()

        self.assertEqual(
            response.headers["HX-Redirect"],
            reverse("cases:case_detail", kwargs={"object_id": str(self.zaak["uuid"])}),
        )

        redirect = self.app.get(response.headers["HX-Redirect"])
        redirect_messages = list(redirect.context["messages"])

        self.assertEqual(redirect_messages[0].message, _("Vraag verstuurd!"))
        self.assertMockMatchersCalled(self.extra_matchers)

        payload = self.matcher_create_contactmoment.request_history[0].json()
        self.assertEqual(
            payload,
            {
                "bronorganisatie": "123456788",
                "kanaal": "Internet",
                "medewerkerIdentificatie": {"identificatie": "FooVonBar"},
                "onderwerp": "afdeling-x",
                "tekst": "Sample text",
                "type": "Melding",
            },
        )

    def test_form_success_with_api_eherkenning_user(self, m):
        self._setUpMocks(m)
        self._setUpExtraMocks(m)

        for use_rsin_for_innNnpId_query_parameter in [True, False]:
            with self.subTest(
                use_rsin_for_innNnpId_query_parameter=use_rsin_for_innNnpId_query_parameter
            ):
                eherkenning_user = eHerkenningUserFactory(
                    kvk="12345678", rsin="000000000"
                )

                config = OpenKlantConfig.get_solo()
                config.use_rsin_for_innNnpId_query_parameter = (
                    use_rsin_for_innNnpId_query_parameter
                )
                config.save()

                identifier = (
                    eherkenning_user.rsin
                    if use_rsin_for_innNnpId_query_parameter
                    else eherkenning_user.kvk
                )
                m.get(
                    f"{KLANTEN_ROOT}klanten?subjectNietNatuurlijkPersoon__innNnpId={identifier}",
                    json=paginated_response([self.klant]),
                ),

                response = self.app.get(self.case_detail_url, user=eherkenning_user)

                form = response.forms["contact-form"]
                form.action = reverse(
                    "cases:case_detail_contact_form",
                    kwargs={"object_id": self.zaak["uuid"]},
                )
                form["question"] = "Sample text"
                response = form.submit()

                self.assertEqual(
                    response.headers["HX-Redirect"],
                    reverse(
                        "cases:case_detail",
                        kwargs={"object_id": str(self.zaak["uuid"])},
                    ),
                )

                redirect = self.app.get(response.headers["HX-Redirect"])
                redirect_messages = list(redirect.context["messages"])

                self.assertEqual(redirect_messages[0].message, _("Vraag verstuurd!"))
                self.assertMockMatchersCalled(self.extra_matchers)

                payload = self.matcher_create_contactmoment.request_history[0].json()
                self.assertEqual(
                    payload,
                    {
                        "bronorganisatie": "123456788",
                        "kanaal": "Internet",
                        "medewerkerIdentificatie": {"identificatie": "FooVonBar"},
                        "onderwerp": "afdeling-x",
                        "tekst": "Sample text",
                        "type": "Melding",
                    },
                )

    def test_form_success_with_email(self, m):
        self._setUpMocks(m)
        self._setUpExtraMocks(m)

        self.ok_config.register_email = "example@example.com"
        self.ok_config.register_contact_moment = False
        self.ok_config.save()

        response = self.app.get(self.case_detail_url, user=self.user)
        form = response.forms["contact-form"]
        form.action = reverse(
            "cases:case_detail_contact_form", kwargs={"object_id": self.zaak["uuid"]}
        )
        form["question"] = "Sample text"
        response = form.submit()

        self.assertEqual(
            response.headers["HX-Redirect"],
            reverse("cases:case_detail", kwargs={"object_id": str(self.zaak["uuid"])}),
        )

        redirect = self.app.get(response.headers["HX-Redirect"])
        redirect_messages = list(redirect.context["messages"])

        self.assertEqual(redirect_messages[0].message, _("Vraag verstuurd!"))

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(
            message.subject,
            _("Contact formulier inzending vanaf Open Inwoner Platform"),
        )

    def test_form_success_with_both_email_and_api(self, m):
        self._setUpMocks(m)
        self._setUpExtraMocks(m)

        self.ok_config.register_email = "example@example.com"
        self.ok_config.save()

        response = self.app.get(self.case_detail_url, user=self.user)
        form = response.forms["contact-form"]
        form.action = reverse(
            "cases:case_detail_contact_form", kwargs={"object_id": self.zaak["uuid"]}
        )
        form["question"] = "Sample text"
        response = form.submit()

        self.assertEqual(
            response.headers["HX-Redirect"],
            reverse("cases:case_detail", kwargs={"object_id": str(self.zaak["uuid"])}),
        )

        redirect = self.app.get(response.headers["HX-Redirect"])
        redirect_messages = list(redirect.context["messages"])

        self.assertEqual(redirect_messages[0].message, _("Vraag verstuurd!"))
        self.assertMockMatchersCalled(self.extra_matchers)
        self.assertEqual(len(mail.outbox), 1)
