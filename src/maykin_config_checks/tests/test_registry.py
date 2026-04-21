from django.test import Client, TestCase
from maykin_config_checks.registry import registry

class ConfigCheckRegistryTests(TestCase):
    def test_can_register_check_without_model(self):
        class DummyCheck:
            identifier = "dummy_check"

        registry.register(DummyCheck)

        check = registry.get_check("dummy_check")

        self.assertEqual(check, DummyCheck)
