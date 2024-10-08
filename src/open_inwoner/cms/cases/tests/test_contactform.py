from unittest.mock import ANY, patch

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

from open_inwoner.accounts.tests.factories import (
    DigidUserFactory,
    eHerkenningUserFactory,
)
from open_inwoner.openklant.clients import ContactmomentenClient
from open_inwoner.openklant.constants import Status
from open_inwoner.openklant.models import OpenKlantConfig
from open_inwoner.openklant.tests.data import CONTACTMOMENTEN_ROOT, KLANTEN_ROOT
from open_inwoner.openzaak.models import CatalogusConfig, OpenZaakConfig
from open_inwoner.openzaak.tests.factories import (
    ServiceFactory,
    ZaakTypeConfigFactory,
    ZGWApiGroupConfigFactory,
)
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
@patch(
    "open_inwoner.cms.cases.views.status.send_contact_confirmation_mail", autospec=True
)
@patch.object(
    ContactmomentenClient,
    "retrieve_objectcontactmomenten_for_zaak",
    autospec=True,
    return_value=[],
)
@override_settings(
    ROOT_URLCONF="open_inwoner.cms.tests.urls", MIDDLEWARE=PATCHED_MIDDLEWARE
)
class CasesContactFormTestCase(AssertMockMatchersMixin, ClearCachesMixin, WebTest):
    def setUp(self):
        super().setUp()

        self.user = DigidUserFactory(bsn="900222086")

        # services
        self.api_group = ZGWApiGroupConfigFactory(
            zrc_service__api_root=ZAKEN_ROOT,
            ztc_service__api_root=CATALOGI_ROOT,
            drc_service__api_root=DOCUMENTEN_ROOT,
            form_service=None,
        )

        # openzaak config
        self.oz_config = OpenZaakConfig.get_solo()
        self.oz_config.document_max_confidentiality = (
            VertrouwelijkheidsAanduidingen.beperkt_openbaar
        )
        self.oz_config.zaak_max_confidentiality = (
            VertrouwelijkheidsAanduidingen.beperkt_openbaar
        )
        self.oz_config.save()

        # openklant config
        self.ok_config = OpenKlantConfig.get_solo()
        self.ok_config.send_email_confirmation = True
        self.ok_config.register_contact_moment = True
        self.ok_config.register_bronorganisatie_rsin = "123456788"
        self.ok_config.register_type = "Melding"
        self.ok_config.register_employee_id = "FooVonBar"
        self.ok_config.register_channel = "the-designated-channel"
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
        self.resultaattype_with_naam = generate_oas_component_cached(
            "ztc",
            "schemas/ResultaatType",
            url=f"{CATALOGI_ROOT}resultaattypen/b1a268dd-4322-47bb-a930-b83066b4a32c",
            zaaktype=self.zaaktype["url"],
            omschrijving="Short description",
            resultaattypeomschrijving="http://example.com",
            selectielijstklasse="http://example.com",
            naam="Long description (>20 chars) of result",
        )
        self.result = generate_oas_component_cached(
            "zrc",
            "schemas/Resultaat",
            uuid="a44153aa-ad2c-6a07-be75-15add5113",
            url=self.zaak["resultaat"],
            # resultaattype=f"{CATALOGI_ROOT}resultaattypen/b1a268dd-4322-47bb-a930-b83066b4a32c",
            resultaattype=self.resultaattype_with_naam["url"],
            zaak=self.zaak["url"],
            toelichting="resultaat toelichting",
        )
        self.klant = generate_oas_component_cached(
            "kc",
            "schemas/Klant",
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
            "cases:case_detail_content",
            kwargs={"object_id": self.zaak["uuid"], "api_group_id": self.api_group.id},
        )

    def _setUpMocks(self, m):
        self.matchers = []

        for resource in [
            self.zaak,
            self.result,
            self.resultaattype_with_naam,
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
            "schemas/Contactmoment",
            url=f"{CONTACTMOMENTEN_ROOT}contactmoment/aaaaaaaa-aaaa-aaaa-aaaa-bbbbbbbbbbbb",
            status=Status.nieuw,
            antwoord="",
            text="hey!\n\nwaddup?",
        )
        self.klant_contactmoment = generate_oas_component_cached(
            "cmc",
            "schemas/Klantcontactmoment",
            url=f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten/aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc",
            klant=self.klant["url"],
            contactmoment=self.contactmoment["url"],
        )
        self.object_contactmoment = generate_oas_component_cached(
            "cmc",
            "schemas/Objectcontactmoment",
            url=f"{CONTACTMOMENTEN_ROOT}contactmoment/aaaaaaaa-aaaa-aaaa-aaaa-bbbbbbbbbbbb",
            contactmoment=self.contactmoment["url"],
            object=self.zaak["url"],
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
        self.matcher_create_objectcontactmoment = m.post(
            f"{CONTACTMOMENTEN_ROOT}objectcontactmomenten",
            json=self.object_contactmoment,
            status_code=201,
        )
        self.extra_matchers = [
            self.matcher_create_contactmoment,
            self.matcher_create_klantcontactmoment,
            self.matcher_create_objectcontactmoment,
        ]

        m.get(
            self.contactmoment["url"],
            json=self.contactmoment,
        )

    def test_form_is_shown_if_open_klant_api_configured(
        self, m, mock_contactmoment, mock_send_confirm
    ):
        self._setUpMocks(m)
        self._setUpExtraMocks(m)

        self.assertTrue(self.ok_config.has_api_configuration())

        response = self.app.get(self.case_detail_url, user=self.user)
        contact_form = response.pyquery("#contact-form")

        self.assertTrue(response.context["case"]["contact_form_enabled"])
        self.assertTrue(contact_form)

        mock_send_confirm.assert_not_called()

    def test_form_is_shown_if_open_klant_email_configured(
        self, m, mock_contactmoment, mock_send_confirm
    ):
        self._setUpMocks(m)
        self._setUpExtraMocks(m)

        self.ok_config.register_email = "example@example.com"
        self.ok_config.register_contact_moment = False
        self.ok_config.save()

        self.assertFalse(self.ok_config.has_api_configuration())
        self.assertTrue(self.ok_config.has_register())

        response = self.app.get(self.case_detail_url, user=self.user)
        contact_form = response.pyquery("#contact-form")

        self.assertTrue(response.context["case"]["contact_form_enabled"])
        self.assertTrue(contact_form)

        mock_send_confirm.assert_not_called()

    def test_form_is_shown_if_open_klant_email_and_api_configured(
        self, m, mock_contactmoment, mock_send_confirm
    ):
        self._setUpMocks(m)
        self._setUpExtraMocks(m)

        self.ok_config.register_email = "example@example.com"
        self.ok_config.save()

        self.assertTrue(self.ok_config.has_api_configuration())
        self.assertTrue(self.ok_config.has_register())

        response = self.app.get(self.case_detail_url, user=self.user)
        contact_form = response.pyquery("#contact-form")

        self.assertTrue(response.context["case"]["contact_form_enabled"])
        self.assertTrue(contact_form)

        mock_send_confirm.assert_not_called()

    def test_no_form_shown_if_open_klant_not_configured(
        self, m, mock_contactmoment, mock_send_confirm
    ):
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

        mock_send_confirm.assert_not_called()

    def test_no_form_shown_if_contact_form_disabled(
        self, m, mock_contactmoment, mock_send_confirm
    ):
        self._setUpMocks(m)
        self._setUpExtraMocks(m)

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

        mock_send_confirm.assert_not_called()

    def test_form_success_with_api(self, m, mock_contactmoment, mock_send_confirm):
        self._setUpMocks(m)
        self._setUpExtraMocks(m)

        response = self.app.get(self.case_detail_url, user=self.user)
        form = response.forms["contact-form"]
        form.action = reverse(
            "cases:case_detail_contact_form",
            kwargs={"object_id": self.zaak["uuid"], "api_group_id": self.api_group.id},
        )
        form["question"] = "Sample text"
        response = form.submit()

        self.assertEqual(
            response.headers["HX-Redirect"],
            reverse(
                "cases:case_detail",
                kwargs={
                    "object_id": str(self.zaak["uuid"]),
                    "api_group_id": self.api_group.id,
                },
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
                "kanaal": "the-designated-channel",
                "medewerkerIdentificatie": {"identificatie": "FooVonBar"},
                "onderwerp": "afdeling-x",
                "tekst": "Sample text",
                "type": "Melding",
            },
        )

        payload = self.matcher_create_objectcontactmoment.request_history[0].json()
        self.assertEqual(
            payload,
            {
                "contactmoment": self.contactmoment["url"],
                "object": self.zaak["url"],
                "objectType": "zaak",
            },
        )

        mock_send_confirm.assert_called_once_with("foo@example.com", ANY)

    def test_form_success_missing_medewerker(
        self, m, mock_contactmoment, mock_send_confirm
    ):
        self._setUpMocks(m)
        self._setUpExtraMocks(m)

        config = OpenKlantConfig.get_solo()
        # empty id should be excluded from contactmoment_create_data
        config.register_employee_id = ""
        config.save()

        response = self.app.get(self.case_detail_url, user=self.user)
        form = response.forms["contact-form"]
        form.action = reverse(
            "cases:case_detail_contact_form",
            kwargs={"object_id": self.zaak["uuid"], "api_group_id": self.api_group.id},
        )
        form["question"] = "Sample text"
        response = form.submit()

        self.assertEqual(
            response.headers["HX-Redirect"],
            reverse(
                "cases:case_detail",
                kwargs={
                    "object_id": str(self.zaak["uuid"]),
                    "api_group_id": self.api_group.id,
                },
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
                "kanaal": "the-designated-channel",
                "onderwerp": "afdeling-x",
                "tekst": "Sample text",
                "type": "Melding",
            },
        )

        payload = self.matcher_create_objectcontactmoment.request_history[0].json()
        self.assertEqual(
            payload,
            {
                "contactmoment": self.contactmoment["url"],
                "object": self.zaak["url"],
                "objectType": "zaak",
            },
        )

        mock_send_confirm.assert_called_once_with("foo@example.com", ANY)

    def test_form_success_with_api_eherkenning_user(
        self, m, mock_contactmoment, mock_send_confirm
    ):
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
                    kwargs={
                        "object_id": self.zaak["uuid"],
                        "api_group_id": self.api_group.id,
                    },
                )
                form["question"] = "Sample text"
                response = form.submit()

                self.assertEqual(
                    response.headers["HX-Redirect"],
                    reverse(
                        "cases:case_detail",
                        kwargs={
                            "object_id": str(self.zaak["uuid"]),
                            "api_group_id": self.api_group.id,
                        },
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
                        "kanaal": "the-designated-channel",
                        "medewerkerIdentificatie": {"identificatie": "FooVonBar"},
                        "onderwerp": "afdeling-x",
                        "tekst": "Sample text",
                        "type": "Melding",
                    },
                )
                # user was modified in loop
                eherkenning_user.refresh_from_db()
                mock_send_confirm.assert_called_once_with(eherkenning_user.email, ANY)
                mock_send_confirm.reset_mock()

    def test_form_success_with_email(self, m, mock_contactmoment, mock_send_confirm):
        self._setUpMocks(m)
        self._setUpExtraMocks(m)

        self.ok_config.register_email = "example@example.com"
        self.ok_config.register_contact_moment = False
        self.ok_config.save()

        response = self.app.get(self.case_detail_url, user=self.user)
        form = response.forms["contact-form"]
        form.action = reverse(
            "cases:case_detail_contact_form",
            kwargs={"object_id": self.zaak["uuid"], "api_group_id": self.api_group.id},
        )
        form["question"] = "Sample text"
        response = form.submit()

        self.assertEqual(
            response.headers["HX-Redirect"],
            reverse(
                "cases:case_detail",
                kwargs={
                    "object_id": str(self.zaak["uuid"]),
                    "api_group_id": self.api_group.id,
                },
            ),
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
        mock_send_confirm.assert_called_once_with("foo@example.com", ANY)

    def test_form_success_with_both_email_and_api(
        self, m, mock_contactmoment, mock_send_confirm
    ):
        self._setUpMocks(m)
        self._setUpExtraMocks(m)

        self.ok_config.register_email = "example@example.com"
        self.ok_config.save()

        response = self.app.get(self.case_detail_url, user=self.user)
        form = response.forms["contact-form"]
        form.action = reverse(
            "cases:case_detail_contact_form",
            kwargs={"object_id": self.zaak["uuid"], "api_group_id": self.api_group.id},
        )
        form["question"] = "Sample text"
        response = form.submit()

        self.assertEqual(
            response.headers["HX-Redirect"],
            reverse(
                "cases:case_detail",
                kwargs={
                    "object_id": str(self.zaak["uuid"]),
                    "api_group_id": self.api_group.id,
                },
            ),
        )

        redirect = self.app.get(response.headers["HX-Redirect"])
        redirect_messages = list(redirect.context["messages"])

        self.assertEqual(redirect_messages[0].message, _("Vraag verstuurd!"))
        self.assertMockMatchersCalled(self.extra_matchers)
        self.assertEqual(len(mail.outbox), 1)

        mock_send_confirm.assert_called_once_with("foo@example.com", ANY)

    def test_send_email_confirmation_is_configurable__send_enabled(
        self, m, mock_contactmoment, mock_send_confirm
    ):
        self._setUpMocks(m)
        self._setUpExtraMocks(m)

        config = OpenKlantConfig.get_solo()
        config.send_email_confirmation = True
        config.save()

        response = self.app.get(self.case_detail_url, user=self.user)
        form = response.forms["contact-form"]
        form.action = reverse(
            "cases:case_detail_contact_form",
            kwargs={"object_id": self.zaak["uuid"], "api_group_id": self.api_group.id},
        )
        form["question"] = "Sample text"
        response = form.submit()
        mock_send_confirm.assert_called_once()

    def test_send_email_confirmation_is_configurable__send_disabled(
        self, m, mock_contactmoment, mock_send_confirm
    ):
        self._setUpMocks(m)
        self._setUpExtraMocks(m)

        config = OpenKlantConfig.get_solo()
        config.send_email_confirmation = False
        config.save()

        response = self.app.get(self.case_detail_url, user=self.user)
        form = response.forms["contact-form"]
        form.action = reverse(
            "cases:case_detail_contact_form",
            kwargs={"object_id": self.zaak["uuid"], "api_group_id": self.api_group.id},
        )
        form["question"] = "Sample text"
        response = form.submit()
        mock_send_confirm.assert_not_called()
