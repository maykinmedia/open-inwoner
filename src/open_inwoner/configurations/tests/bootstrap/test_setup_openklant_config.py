from pathlib import Path

from django.test import TestCase

from django_setup_configuration.exceptions import ConfigurationRunFailed
from django_setup_configuration.test_utils import execute_single_step
from zgw_consumers.constants import APITypes

from open_inwoner.configurations.bootstrap.openklant import (
    KlantenSysteemConfigurationStep,
)
from open_inwoner.openklant.constants import KlantenServiceType
from open_inwoner.openklant.models import (
    ContactFormSubject,
    ESuiteKlantConfig,
    KlantenSysteemConfig,
    OpenKlant2Config,
)
from open_inwoner.openzaak.tests.factories import ServiceFactory

KLANTEN_SERVICE_API_ROOT = "https://openklant.local/klanten/api/v1/"
CONTACTMOMENTEN_SERVICE_API_ROOT = "https://openklant.local/contactmomenten/api/v1/"

BASE_DIR = Path(__file__).parent / "files"
KLANTENSYSTEEM_CONFIG_STEP_FULL_YAML = str(
    BASE_DIR / "klantensysteem_config_step_full.yaml"
)
KLANTENSYSTEEM_CONFIG_STEP_WITH_ESUITE_YAML = str(
    BASE_DIR / "klantensysteem_config_step_with_esuite.yaml"
)
KLANTENSYSTEEM_CONFIG_STEP_WITH_OPENKLANT2_YAML = str(
    BASE_DIR / "klantensysteem_config_step_with_openklant2.yaml"
)


class KlantenSysteemConfigurationStepTest(TestCase):
    def test_configure_basic_klantensysteem_without_nested_configs(self):
        kc = ServiceFactory(
            slug="klanten-service",
            api_root=KLANTEN_SERVICE_API_ROOT,
            api_type=APITypes.kc,
        )
        cmc = ServiceFactory(
            slug="contactmomenten-service",
            api_root=CONTACTMOMENTEN_SERVICE_API_ROOT,
            api_type=APITypes.cmc,
        )
        esuite_config = ESuiteKlantConfig.get_solo()
        esuite_config.klanten_service = kc
        esuite_config.contactmomenten_service = cmc
        esuite_config.save()

        execute_single_step(
            KlantenSysteemConfigurationStep,
            yaml_source=KLANTENSYSTEEM_CONFIG_STEP_FULL_YAML,
        )

        config = KlantenSysteemConfig.get_solo()
        self.assertEqual(config.primary_backend, KlantenServiceType.ESUITE.value)
        self.assertTrue(config.register_contact_via_api)
        self.assertEqual(config.register_contact_email, "oip-test@test.nl")
        self.assertTrue(config.send_email_confirmation)

    def test_configure_fails_when_required_api_services_missing(self):
        with self.assertRaises(ConfigurationRunFailed) as exc:
            execute_single_step(
                KlantenSysteemConfigurationStep,
                yaml_source=KLANTENSYSTEEM_CONFIG_STEP_FULL_YAML,
            )

        self.assertEqual(
            str(exc.exception), "Unable to validate and save KlantenSysteemConfig"
        )

    def test_configure_with_nested_esuite_config(self):
        kc = ServiceFactory(
            slug="klanten-service",
            api_root=KLANTEN_SERVICE_API_ROOT,
            api_type=APITypes.kc,
        )
        cmc = ServiceFactory(
            slug="contactmomenten-service",
            api_root=CONTACTMOMENTEN_SERVICE_API_ROOT,
            api_type=APITypes.cmc,
        )

        execute_single_step(
            KlantenSysteemConfigurationStep,
            yaml_source=KLANTENSYSTEEM_CONFIG_STEP_WITH_ESUITE_YAML,
        )

        klanten_config = KlantenSysteemConfig.get_solo()
        self.assertEqual(
            klanten_config.primary_backend, KlantenServiceType.ESUITE.value
        )
        self.assertTrue(klanten_config.register_contact_via_api)
        self.assertEqual(klanten_config.register_contact_email, "oip-test@test.nl")
        self.assertTrue(klanten_config.send_email_confirmation)

        esuite_config = ESuiteKlantConfig.get_solo()
        self.assertEqual(esuite_config.klanten_service, kc)
        self.assertEqual(esuite_config.contactmomenten_service, cmc)
        self.assertEqual(esuite_config.register_bronorganisatie_rsin, "837194569")
        self.assertEqual(esuite_config.register_channel, "email")
        self.assertEqual(esuite_config.register_type, "bericht")
        self.assertEqual(esuite_config.register_employee_id, "1234")
        self.assertEqual(esuite_config.use_rsin_for_innNnpId_query_parameter, True)

        subjects = list(
            ContactFormSubject.objects.filter(esuite_config=esuite_config).order_by(
                "order"
            )
        )
        self.assertEqual([s.subject for s in subjects], ["Algemene vraag", "Klacht"])
        self.assertEqual(
            [s.esuite_subject_code for s in subjects], ["algemeen", "klacht"]
        )

    def test_configure_esuite_fails_with_nonexistent_service_identifiers(self):
        ServiceFactory(
            slug="klanten-service-different-from-yaml",
            api_root=KLANTEN_SERVICE_API_ROOT,
            api_type=APITypes.kc,
        )
        ServiceFactory(
            slug="contactmomenten-service-different-from-yaml",
            api_root=CONTACTMOMENTEN_SERVICE_API_ROOT,
            api_type=APITypes.cmc,
        )

        with self.assertRaises(ConfigurationRunFailed) as exc:
            execute_single_step(
                KlantenSysteemConfigurationStep,
                yaml_source=KLANTENSYSTEEM_CONFIG_STEP_WITH_ESUITE_YAML,
            )

        self.assertEqual(
            str(exc.exception),
            (
                "Unable to retrieve `klanten_service` and/or `contactmomenten_service`"
                ". Try first configuring the `zgw_consumers` configuration steps, and."
                " ensure that both the `identifier` and `api_type` fields match."
            ),
        )

    def test_configure_esuite_fails_with_wrong_klanten_service_api_type(self):
        ServiceFactory(
            slug="klanten-service",
            api_root=KLANTEN_SERVICE_API_ROOT,
            api_type=APITypes.orc,
        )
        ServiceFactory(
            slug="contactmomenten-service",
            api_root=CONTACTMOMENTEN_SERVICE_API_ROOT,
            api_type=APITypes.cmc,
        )

        with self.assertRaises(ConfigurationRunFailed) as exc:
            execute_single_step(
                KlantenSysteemConfigurationStep,
                yaml_source=KLANTENSYSTEEM_CONFIG_STEP_WITH_ESUITE_YAML,
            )

        self.assertEqual(
            str(exc.exception),
            (
                "Found klanten service with identifier `klanten-service`, but expected"
                " `api_type` to equal `kc` and got `orc`"
            ),
        )

    def test_configure_esuite_fails_with_wrong_contactmomenten_service_api_type(self):
        ServiceFactory(
            slug="klanten-service",
            api_root=KLANTEN_SERVICE_API_ROOT,
            api_type=APITypes.kc,
        )
        ServiceFactory(
            slug="contactmomenten-service",
            api_root=CONTACTMOMENTEN_SERVICE_API_ROOT,
            api_type=APITypes.orc,
        )

        with self.assertRaises(ConfigurationRunFailed) as exc:
            execute_single_step(
                KlantenSysteemConfigurationStep,
                yaml_source=KLANTENSYSTEEM_CONFIG_STEP_WITH_ESUITE_YAML,
            )

        self.assertEqual(
            str(exc.exception),
            (
                "Found contactmomenten service with identifier "
                "`contactmomenten-service`, but expected `api_type` to equal `cmc`"
                " and got `orc`"
            ),
        )

    def test_configure_esuite_is_idempotent_and_overwrites_modified_values(self):
        kc = ServiceFactory(
            slug="klanten-service",
            api_root=KLANTEN_SERVICE_API_ROOT,
            api_type=APITypes.kc,
        )
        cmc = ServiceFactory(
            slug="contactmomenten-service",
            api_root=CONTACTMOMENTEN_SERVICE_API_ROOT,
            api_type=APITypes.cmc,
        )

        def assert_values():
            config = ESuiteKlantConfig.get_solo()

            self.assertEqual(config.klanten_service, kc)
            self.assertEqual(config.contactmomenten_service, cmc)

            self.assertEqual(config.register_bronorganisatie_rsin, "837194569")
            self.assertEqual(config.register_channel, "email")
            self.assertEqual(config.register_type, "bericht")
            self.assertEqual(config.register_employee_id, "1234")
            self.assertEqual(config.use_rsin_for_innNnpId_query_parameter, True)

        execute_single_step(
            KlantenSysteemConfigurationStep,
            yaml_source=KLANTENSYSTEEM_CONFIG_STEP_WITH_ESUITE_YAML,
        )

        assert_values()

        config = ESuiteKlantConfig.get_solo()
        config.register_bronorganisatie_rsin = "800000009"
        config.register_channel = "not-email"
        config.register_type = "not-bericht"
        config.register_employee_id = "4321"
        config.use_rsin_for_innNnpId_query_parameter = False
        config.save()

        execute_single_step(
            KlantenSysteemConfigurationStep,
            yaml_source=KLANTENSYSTEEM_CONFIG_STEP_WITH_ESUITE_YAML,
        )

        assert_values()

    def test_configure_with_nested_openklant2_config(self):
        kc = ServiceFactory(
            slug="klanten-service",
            api_root=KLANTEN_SERVICE_API_ROOT,
            api_type=APITypes.kc,
        )

        execute_single_step(
            KlantenSysteemConfigurationStep,
            yaml_source=KLANTENSYSTEEM_CONFIG_STEP_WITH_OPENKLANT2_YAML,
        )

        klanten_config = KlantenSysteemConfig.get_solo()
        self.assertEqual(
            klanten_config.primary_backend, KlantenServiceType.OPENKLANT2.value
        )
        self.assertTrue(klanten_config.register_contact_via_api)
        self.assertEqual(klanten_config.register_contact_email, "oip-test@test.nl")
        self.assertTrue(klanten_config.send_email_confirmation)

        openklant2_config = OpenKlant2Config.get_solo()
        self.assertEqual(openklant2_config.service, kc)
        self.assertEqual(openklant2_config.mijn_vragen_kanaal, "formulier")
        self.assertEqual(openklant2_config.mijn_vragen_organisatie_naam, "De Gemeente")
        self.assertEqual(
            str(openklant2_config.mijn_vragen_actor),
            "e412c6f6-bc31-4fd4-b883-0fb5e88d3f5b",
        )
        self.assertEqual(
            openklant2_config.interne_taak_gevraagde_handeling, "Vraag beantwoorden"
        )
        self.assertEqual(
            openklant2_config.interne_taak_toelichting,
            "Vraag via OIP, graag beantwoorden",
        )

        subjects = list(
            ContactFormSubject.objects.filter(
                openklant_config=openklant2_config
            ).order_by("order")
        )
        self.assertEqual([s.subject for s in subjects], ["Algemene vraag", "Klacht"])
        self.assertTrue(all(s.esuite_subject_code is None for s in subjects))

    def test_configure_openklant2_subjects_are_replaced_on_rerun(self):
        """
        A re-run with a different subject list replaces the old one rather than
        appending to it -- and rather than leaving it as the admin may have
        edited it, the same rule the rest of this step follows.
        """
        ServiceFactory(
            slug="klanten-service",
            api_root=KLANTEN_SERVICE_API_ROOT,
            api_type=APITypes.kc,
        )
        execute_single_step(
            KlantenSysteemConfigurationStep,
            yaml_source=KLANTENSYSTEEM_CONFIG_STEP_WITH_OPENKLANT2_YAML,
        )
        config = OpenKlant2Config.get_solo()
        ContactFormSubject.objects.create(
            subject="Admin-added subject", openklant_config=config
        )

        execute_single_step(
            KlantenSysteemConfigurationStep,
            yaml_source=KLANTENSYSTEEM_CONFIG_STEP_WITH_OPENKLANT2_YAML,
        )

        subjects = ContactFormSubject.objects.filter(openklant_config=config)
        self.assertEqual(
            sorted(s.subject for s in subjects), ["Algemene vraag", "Klacht"]
        )

    def test_configure_openklant2_subjects_omitted_leaves_existing_alone(self):
        """
        Subjects are only touched when the config says something about them --
        the same "omitted means leave it alone" rule as everywhere else in
        setup-configuration that doesn't overwrite unconditionally.
        """
        kc = ServiceFactory(
            slug="klanten-service",
            api_root=KLANTEN_SERVICE_API_ROOT,
            api_type=APITypes.kc,
        )
        execute_single_step(
            KlantenSysteemConfigurationStep,
            yaml_source=KLANTENSYSTEEM_CONFIG_STEP_WITH_OPENKLANT2_YAML,
        )
        config = OpenKlant2Config.get_solo()

        execute_single_step(
            KlantenSysteemConfigurationStep,
            object_source={
                "klantensysteem_config_enable": True,
                "klantensysteem_config": {
                    "primary_backend": "openklant2",
                    "register_contact_via_api": True,
                    "register_contact_email": "oip-test@test.nl",
                    "openklant2_config": {
                        "service_identifier": kc.slug,
                        "mijn_vragen_actor": "e412c6f6-bc31-4fd4-b883-0fb5e88d3f5b",
                    },
                },
            },
        )

        subjects = ContactFormSubject.objects.filter(openklant_config=config)
        self.assertEqual(
            sorted(s.subject for s in subjects), ["Algemene vraag", "Klacht"]
        )

    def test_configure_openklant2_is_idempotent_and_overwrites_modified_values(self):
        kc = ServiceFactory(
            slug="klanten-service",
            api_root=KLANTEN_SERVICE_API_ROOT,
            api_type=APITypes.kc,
        )

        def assert_values():
            config = OpenKlant2Config.get_solo()

            self.assertEqual(config.service, kc)
            self.assertEqual(config.mijn_vragen_kanaal, "formulier")
            self.assertEqual(config.mijn_vragen_organisatie_naam, "De Gemeente")
            self.assertEqual(
                str(config.mijn_vragen_actor), "e412c6f6-bc31-4fd4-b883-0fb5e88d3f5b"
            )
            self.assertEqual(
                config.interne_taak_gevraagde_handeling, "Vraag beantwoorden"
            )
            self.assertEqual(
                config.interne_taak_toelichting, "Vraag via OIP, graag beantwoorden"
            )

        execute_single_step(
            KlantenSysteemConfigurationStep,
            yaml_source=KLANTENSYSTEEM_CONFIG_STEP_WITH_OPENKLANT2_YAML,
        )

        assert_values()

        config = OpenKlant2Config.get_solo()
        config.mijn_vragen_kanaal = "not-formulier"
        config.mijn_vragen_organisatie_naam = "Not De Gemeente"
        config.interne_taak_gevraagde_handeling = "Not vraag beantwoorden"
        config.interne_taak_toelichting = "Not vraag via OIP"
        config.save()

        execute_single_step(
            KlantenSysteemConfigurationStep,
            yaml_source=KLANTENSYSTEEM_CONFIG_STEP_WITH_OPENKLANT2_YAML,
        )

        assert_values()
