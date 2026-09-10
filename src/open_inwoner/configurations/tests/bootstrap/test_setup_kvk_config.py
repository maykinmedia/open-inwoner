from pathlib import Path

from django.test import TestCase

from django_setup_configuration.exceptions import ConfigurationRunFailed
from django_setup_configuration.test_utils import execute_single_step

from open_inwoner.configurations.bootstrap.kvk import KvKConfigurationStep
from open_inwoner.kvk.models import KvKConfig

BASE_DIR = Path(__file__).parent / "files"
KVK_CONFIG_STEP_FULL_YAML = str(BASE_DIR / "kvk_config_step_full.yaml")
KVK_CONFIG_STEP_MINIMAL_YAML = str(BASE_DIR / "kvk_config_step_minimal.yaml")
KVK_CONFIG_STEP_INVALID_API_ROOT_YAML = str(
    BASE_DIR / "kvk_config_step_invalid_api_root.yaml"
)


class KvKConfigurationStepTest(TestCase):
    def test_configure_with_full_config(self):
        execute_single_step(
            KvKConfigurationStep,
            yaml_source=KVK_CONFIG_STEP_FULL_YAML,
        )

        config = KvKConfig.get_solo()
        self.assertEqual(config.api_root, "https://api.kvk.nl/test/api/")
        self.assertEqual(config.api_key, "dummy-api-key")

    def test_configure_with_minimal_config_leaves_omitted_fields_untouched(self):
        config = KvKConfig.get_solo()
        config.api_key = "existing-key"
        config.save()

        execute_single_step(
            KvKConfigurationStep,
            yaml_source=KVK_CONFIG_STEP_MINIMAL_YAML,
        )

        config = KvKConfig.get_solo()
        self.assertEqual(config.api_root, "https://api.kvk.nl/test/api/")
        # not present in the minimal YAML, so left as it was
        self.assertEqual(config.api_key, "existing-key")

    def test_configure_fails_with_invalid_api_root(self):
        with self.assertRaises(ConfigurationRunFailed):
            execute_single_step(
                KvKConfigurationStep,
                yaml_source=KVK_CONFIG_STEP_INVALID_API_ROOT_YAML,
            )

    def test_configure_is_idempotent(self):
        for _ in range(2):
            execute_single_step(
                KvKConfigurationStep,
                yaml_source=KVK_CONFIG_STEP_FULL_YAML,
            )

        config = KvKConfig.get_solo()
        self.assertEqual(config.api_root, "https://api.kvk.nl/test/api/")
        self.assertEqual(config.api_key, "dummy-api-key")
