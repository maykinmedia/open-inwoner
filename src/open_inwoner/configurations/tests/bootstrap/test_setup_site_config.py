from pathlib import Path

from django.test import TestCase

import yaml
from django_setup_configuration.exceptions import (
    ConfigurationRunFailed,
    PrerequisiteFailed,
)
from django_setup_configuration.test_utils import execute_single_step

from open_inwoner.configurations.bootstrap.siteconfig import (
    EXCLUDED_FIELDS,
    SiteConfigurationModel,
    SiteConfigurationStep,
)
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.configurations.tests.factories import SiteConfigurationFactory
from open_inwoner.utils.css import clean_stylesheet

BASE_DIR = Path(__file__).parent / "files"
SITE_CONFIG_STEP_FULL = str(BASE_DIR / "site_config_step_full.yaml")
SITE_CONFIG_STEP_MINIMAL = str(BASE_DIR / "site_config_step_minimal.yaml")
SITE_CONFIG_STEP_INVALID_REDIRECT = str(
    BASE_DIR / "site_config_step_invalid_redirect.yaml"
)
SITE_CONFIG_STEP_MISSING_NAME = str(BASE_DIR / "site_config_step_missing_name.yaml")

# Fields whose underlying model attribute is a ProsemirrorFieldDocument wrapper
# rather than the plain value stored in YAML: the YAML value is HTML, applied
# through the wrapper's `.html` setter.
RICH_TEXT_FIELDS = frozenset(
    {"warning_banner_text", "login_text", "search_zero_results_text"}
)


class SiteConfigurationModelTests(TestCase):
    def test_every_configurable_field_is_covered(self):
        """
        Every field on SiteConfiguration is either configurable through this
        step or explicitly excluded, so the two can never silently drift apart
        as fields are added to the model.
        """
        model_fields = set(SiteConfigurationModel.model_fields)
        django_fields = {
            field.name
            for field in SiteConfiguration._meta.get_fields()
            if field.concrete and field.name != "id"
        }

        self.assertFalse(model_fields & EXCLUDED_FIELDS)
        self.assertEqual(model_fields | EXCLUDED_FIELDS, django_fields)


class SiteConfigurationStepTests(TestCase):
    def test_configure_full_sets_every_field(self):
        execute_single_step(SiteConfigurationStep, yaml_source=SITE_CONFIG_STEP_FULL)

        config = SiteConfiguration.get_solo()
        expected = yaml.safe_load(Path(SITE_CONFIG_STEP_FULL).read_text())[
            "site_config"
        ]

        for field, value in expected.items():
            actual = getattr(config, field)
            if field in RICH_TEXT_FIELDS:
                actual = actual.html
            elif field == "extra_css":
                # SiteConfiguration.save() rewrites the stylesheet through a
                # CSS cleaner, so the stored value isn't a byte-for-byte copy
                value = clean_stylesheet(value)
            with self.subTest(field=field):
                self.assertEqual(actual, value)

    def test_configure_is_idempotent(self):
        execute_single_step(SiteConfigurationStep, yaml_source=SITE_CONFIG_STEP_FULL)
        execute_single_step(SiteConfigurationStep, yaml_source=SITE_CONFIG_STEP_FULL)

        self.assertEqual(SiteConfiguration.objects.count(), 1)
        config = SiteConfiguration.get_solo()
        self.assertEqual(config.name, "Test Municipality")

    def test_rerun_with_a_different_value_overwrites_the_admin_edit(self):
        """
        Simulates an admin editing a field after it was bootstrapped:
        re-running the step overwrites that edit.
        """
        execute_single_step(SiteConfigurationStep, yaml_source=SITE_CONFIG_STEP_FULL)
        config = SiteConfiguration.get_solo()
        config.contact_phonenumber = "0699999999"
        config.save()

        execute_single_step(SiteConfigurationStep, yaml_source=SITE_CONFIG_STEP_FULL)

        config.refresh_from_db()
        self.assertEqual(config.contact_phonenumber, "0612345678")

    def test_omitted_field_resets_to_its_default(self):
        """
        A run that doesn't mention a field resets it to the model default,
        the same as it does for every other field this step manages.
        """
        SiteConfigurationFactory(name="Baseline Municipality", clamav_port=9999)

        execute_single_step(SiteConfigurationStep, yaml_source=SITE_CONFIG_STEP_MINIMAL)

        config = SiteConfiguration.get_solo()
        self.assertEqual(config.name, "Minimal Municipality")
        self.assertEqual(config.clamav_port, 3310)

    def test_invalid_redirect_to_raises_configuration_run_failed(self):
        with self.assertRaises(ConfigurationRunFailed):
            execute_single_step(
                SiteConfigurationStep, yaml_source=SITE_CONFIG_STEP_INVALID_REDIRECT
            )

    def test_missing_name_raises_prerequisite_failed(self):
        """
        `name` has no sensible default (unlike every other field this step
        manages), so it must always be provided.
        """
        with self.assertRaises(PrerequisiteFailed):
            execute_single_step(
                SiteConfigurationStep, yaml_source=SITE_CONFIG_STEP_MISSING_NAME
            )


def _configure_warning_banner_text(value: str | None = None) -> None:
    site_config = {"name": "Test Municipality"}
    if value is not None:
        site_config["warning_banner_text"] = value
    execute_single_step(
        SiteConfigurationStep,
        object_source={"site_config_enable": True, "site_config": site_config},
    )


class WarningBannerTextFieldTests(TestCase):
    """Dedicated test for a `ProsemirrorModelField`."""

    def test_allowed_formatting_round_trips_through_the_database(self):
        html = (
            "<p>Let op: <strong>onderhoud</strong> gepland op "
            '<a href="https://example.org">deze pagina</a>.</p>'
        )
        _configure_warning_banner_text(html)

        config = SiteConfiguration.get_solo()
        config.refresh_from_db()
        self.assertEqual(config.warning_banner_text.html, html)

    def test_disallowed_html_is_downgraded_instead_of_raising(self):
        """
        The field only allows paragraphs/hard breaks and a handful of marks.
        Content using anything else (headings, lists, ...) is downgraded to
        plain paragraphs by the ProseMirror HTML parser rather than raising
        -- the step must not assume `full_clean()` catches this, since
        `ProsemirrorModelField.validate()` doesn't check node/mark types.
        """
        _configure_warning_banner_text("<h1>Title</h1><ul><li>item</li></ul>")

        config = SiteConfiguration.get_solo()
        config.refresh_from_db()
        self.assertEqual(config.warning_banner_text.html, "<p>Title</p><p>item</p>")

    def test_rerun_with_a_different_value_overwrites_the_admin_edit(self):
        _configure_warning_banner_text("<p>Origineel.</p>")
        config = SiteConfiguration.get_solo()
        config.warning_banner_text = "<p>Admin-edited.</p>"
        config.save()

        _configure_warning_banner_text("<p>Origineel.</p>")

        config.refresh_from_db()
        self.assertEqual(config.warning_banner_text.html, "<p>Origineel.</p>")

    def test_omitted_field_resets_to_empty(self):
        _configure_warning_banner_text("<p>Origineel.</p>")

        _configure_warning_banner_text(None)

        config = SiteConfiguration.get_solo()
        config.refresh_from_db()
        self.assertEqual(config.warning_banner_text.html, "")
