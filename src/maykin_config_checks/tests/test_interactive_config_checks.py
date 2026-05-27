from unittest.mock import patch

from django import forms
from django.contrib.auth import get_user_model
from django.test import TestCase

from maykin_config_checks import GenericConfigCheckResult
from maykin_config_checks.registry import registry

User = get_user_model()


class MinimalForm(forms.Form):
    pass


class FormWithField(forms.Form):
    name = forms.CharField(max_length=100)


class AlwaysAllowPermission:
    def has_permission(self, request, obj=None):
        return True

    def get_error_message(self, obj=None):
        return ""  # pragma: no cover


class AlwaysDenyPermission:
    def has_permission(self, request, obj=None):
        return False

    def get_error_message(self, obj=None):
        return "Permission denied: missing API key"


class MinimalCheck:
    identifier = "test_minimal_check"
    label = "Minimal Check"
    form_class = MinimalForm
    required_permissions = [AlwaysAllowPermission()]

    @classmethod
    def get_form_kwargs(cls, instance=None):
        return {}

    def run(self, data, instance=None, request=None):
        return GenericConfigCheckResult(
            success=True,
            identifier=self.identifier,
            verbose_name=self.label,
            message="All good",
        )


class CheckWithField:
    identifier = "test_check_with_field"
    label = "Check With Field"
    form_class = FormWithField
    required_permissions = [AlwaysAllowPermission()]

    @classmethod
    def get_form_kwargs(cls, instance=None):
        return {}

    def run(self, data, instance=None, request=None):
        return GenericConfigCheckResult(
            success=True,
            identifier=self.identifier,
            verbose_name=self.label,
            message=f"Hello, {data['name']}",
        )


class FailingPermissionCheck:
    identifier = "test_failing_perm_check"
    label = "Failing Permission Check"
    form_class = MinimalForm
    required_permissions = [AlwaysDenyPermission()]

    @classmethod
    def get_form_kwargs(cls, instance=None):
        return {}

    def run(self, data, instance=None, request=None):  # pragma: no cover
        return GenericConfigCheckResult(
            success=False,
            identifier=self.identifier,
            verbose_name=self.label,
            message="Should not reach here",
        )


class MissingFormClassCheck:
    identifier = "test_no_form_class_check"
    label = "No form_class Check"
    required_permissions = []

    @classmethod
    def get_form_kwargs(cls, instance=None):
        return {}


class MissingRequiredPermissionsCheck:
    identifier = "test_no_perms_attr_check"
    label = "No required_permissions Check"
    form_class = MinimalForm

    @classmethod
    def get_form_kwargs(cls, instance=None):
        return {}


class ConfigCheckTestCase(TestCase):
    def setUp(self):
        super().setUp()

        self._original_checks = dict(registry._checks)
        self._original_model_checks = {
            k: set(v) for k, v in registry._model_checks.items()
        }
        registry.register(MinimalCheck)
        registry.register(CheckWithField)
        registry.register(FailingPermissionCheck)
        registry.register(MissingFormClassCheck)
        registry.register(MissingRequiredPermissionsCheck)

        self.staff_user = User.objects.create_user(
            email="staff@example.com",
            password="secret",
            is_staff=True,
        )
        self.regular_user = User.objects.create_user(
            email="regular@example.com",
            password="secret",
            is_staff=False,
        )

    def tearDown(self):
        super().tearDown()
        registry._checks = self._original_checks
        registry._model_checks = self._original_model_checks


class RunConfigCheckAccessTests(ConfigCheckTestCase):
    def test_anonymous_user_is_denied(self):
        response = self.client.get(f"/admin/config-check/{MinimalCheck.identifier}/")

        self.assertEqual(response.status_code, 403)

    def test_non_staff_user_is_denied(self):
        self.client.force_login(self.regular_user)

        response = self.client.get(f"/admin/config-check/{MinimalCheck.identifier}/")

        self.assertEqual(response.status_code, 403)

    def test_staff_user_can_access(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(f"/admin/config-check/{MinimalCheck.identifier}/")

        self.assertEqual(response.status_code, 200)


class RunConfigCheckGuardTests(ConfigCheckTestCase):
    def test_unknown_check_id_returns_404(self):
        self.client.force_login(self.staff_user)

        response = self.client.get("/admin/config-check/does_not_exist/")

        self.assertEqual(response.status_code, 404)

    def test_check_without_form_class_raises_value_error(self):
        self.client.force_login(self.staff_user)

        with self.assertRaises(ValueError):
            self.client.get(f"/admin/config-check/{MissingFormClassCheck.identifier}/")

    def test_check_without_required_permissions_raises_value_error(self):
        self.client.force_login(self.staff_user)

        with self.assertRaises(ValueError):
            self.client.get(
                f"/admin/config-check/{MissingRequiredPermissionsCheck.identifier}/"
            )

    def test_failing_required_permission_returns_403(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(
            f"/admin/config-check/{FailingPermissionCheck.identifier}/"
        )

        self.assertEqual(response.status_code, 403)
        self.assertIn(
            AlwaysDenyPermission().get_error_message(),
            response.content.decode(),
        )


class RunConfigCheckFormTests(ConfigCheckTestCase):
    def test_get_renders_form_without_result(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(f"/admin/config-check/{MinimalCheck.identifier}/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)
        self.assertIsNone(response.context["result"])

    def test_post_runs_check_and_returns_result(self):
        self.client.force_login(self.staff_user)

        response = self.client.post(
            f"/admin/config-check/{MinimalCheck.identifier}/",
            data={},
        )

        self.assertEqual(response.status_code, 200)
        result = response.context["result"]
        self.assertIsNotNone(result)
        self.assertTrue(result.success)
        self.assertEqual(result.message, "All good")

    def test_post_with_valid_field_data_passes_cleaned_data_to_run(self):
        self.client.force_login(self.staff_user)
        mock_result = GenericConfigCheckResult(
            success=True,
            identifier=CheckWithField.identifier,
            verbose_name=CheckWithField.label,
            message="mocked",
        )

        with patch.object(CheckWithField, "run", return_value=mock_result) as mock_run:
            response = self.client.post(
                f"/admin/config-check/{CheckWithField.identifier}/",
                data={"name": "Alice"},
            )

        self.assertEqual(response.status_code, 200)
        mock_run.assert_called_once()
        # MagicMock is not a descriptor, so self is not forwarded; only cleaned_data is passed
        (passed_data,) = mock_run.call_args.args
        self.assertEqual(passed_data, {"name": "Alice"})

    def test_post_with_invalid_field_data_does_not_call_run(self):
        self.client.force_login(self.staff_user)

        with patch.object(CheckWithField, "run") as mock_run:
            response = self.client.post(
                f"/admin/config-check/{CheckWithField.identifier}/",
                data={"name": ""},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["result"])
        self.assertFalse(response.context["form"].is_valid())
        mock_run.assert_not_called()
