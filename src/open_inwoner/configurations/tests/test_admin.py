from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms.models import model_to_dict
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.datastructures import MultiValueDict
from django.utils.translation import gettext_lazy as _

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from open_inwoner.accounts.tests.factories import UserFactory

from ..admin import (
    SiteConfigurationAdmin,
    SiteConfigurationAdminForm,
)
from ..models import SiteConfiguration
from ..validators import validate_javascript_file


@disable_admin_mfa()
class TestAdminSite(WebTest):
    csrf_checks = False

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(is_superuser=True, is_staff=True)

    def test_site_add_prevented_if_one_exists(self):
        """Test that adding a site is prevented if one already exists."""
        # Make sure we have exactly one site
        initial_site_count = Site.objects.count()
        self.assertEqual(initial_site_count, 1)

        response = self.app.get(
            reverse("admin:sites_site_add"), user=self.user, expect_errors=True
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Site.objects.count(), initial_site_count)

    def test_site_deletion_prevented(self):
        """Test that site deletion is prevented."""
        site = Site.objects.get()

        response = self.app.get(
            reverse("admin:sites_site_change", args=[site.pk]), user=self.user
        )

        # Verify the delete button is not present (text or link)
        self.assertNotIn("Delete", response.text)
        delete_url = reverse("admin:sites_site_delete", args=[site.pk])
        self.assertNotIn(delete_url, response.text)

        # Try to access the delete page directly - should return 403 Forbidden
        response = self.app.get(delete_url, user=self.user, expect_errors=True)
        self.assertEqual(response.status_code, 403)

        # Verify the site still exists
        self.assertTrue(Site.objects.filter(pk=site.pk).exists())


@disable_admin_mfa()
class TestAdminForm(WebTest):
    def setUp(self):
        self.user = UserFactory(is_superuser=True, is_staff=True)
        self.form = self.app.get(
            reverse("admin:configurations_siteconfiguration_change"), user=self.user
        ).forms["siteconfiguration_form"]
        self.form["name"] = "xyz"
        self.form["primary_color"] = "#FFFFFF"
        self.form["primary_font_color"] = "#FFFFFF"
        self.form["secondary_color"] = "#FFFFFF"
        self.form["secondary_font_color"] = "#FFFFFF"
        self.form["accent_color"] = "#FFFFFF"
        self.form["accent_font_color"] = "#FFFFFF"
        # django-jsonform requires JS to work properly and with Webtest the default
        # value for ArrayFields is an empty string, causing it crash to when trying to parse
        # that value as JSON
        self.form["recipients_email_digest"] = "[]"

    def test_valid_path_is_saved(self):
        config = SiteConfiguration.get_solo()
        self.assertIsNone(config.redirect_to)

        self.form["redirect_to"] = "/accounts/login/"
        self.form.submit()

        config.refresh_from_db()

        self.assertEqual(config.redirect_to, "/accounts/login/")

    def test_invalid_path_is_not_saved(self):
        config = SiteConfiguration.get_solo()
        self.assertIsNone(config.redirect_to)

        self.form["redirect_to"] = "/invalid/path"
        response = self.form.submit()

        config.refresh_from_db()

        self.assertIsNone(config.redirect_to)
        self.assertEqual(
            response.context["errors"], [[_("The entered path is invalid.")]]
        )

    def test_valid_url_is_saved(self):
        config = SiteConfiguration.get_solo()
        self.assertIsNone(config.redirect_to)

        self.form["redirect_to"] = "https://www.example.com"
        self.form.submit()

        config.refresh_from_db()

        self.assertEqual(config.redirect_to, "https://www.example.com")

    def test_invalid_url_is_not_saved(self):
        config = SiteConfiguration.get_solo()
        self.assertIsNone(config.redirect_to)

        self.form["redirect_to"] = "invalid-url.com"
        response = self.form.submit()

        config.refresh_from_db()

        self.assertIsNone(config.redirect_to)
        self.assertEqual(
            response.context["errors"], [[_("The entered url is invalid.")]]
        )

    def test_email_verification_requires_message(self):
        """Test that email verification requires a message."""
        config = SiteConfiguration.get_solo()

        self.form["email_verification_required"] = True
        self.form["email_verification_message"] = ""
        response = self.form.submit()

        self.assertIn(
            "Email verification message cannot be empty if email verification is required",
            response.text,
        )

        config.refresh_from_db()
        self.assertFalse(config.email_verification_required)


class CustomJavaScriptValidatorTests(TestCase):
    """Test the JavaScript file validator"""

    def test_valid_javascript_file(self):
        """Test that valid JavaScript passes validation"""
        valid_js_content = """
        // Valid JavaScript
        console.log('Hello world');
        alert('This is valid');
        var message = 'Test message';
        """
        js_file = SimpleUploadedFile(
            "valid.js",
            valid_js_content.encode("utf-8"),
            content_type="application/javascript",
        )

        result = validate_javascript_file(js_file)
        self.assertEqual(result, js_file)

    def test_file_too_large(self):
        """Test that files larger than 0.5MB are rejected"""
        large_content = "// " + "x" * (1024 * 512 + 1)
        large_file = SimpleUploadedFile(
            "large.js",
            large_content.encode("utf-8"),
            content_type="application/javascript",
        )

        with self.assertRaises(ValidationError) as context:
            validate_javascript_file(large_file)

        error_message = str(context.exception)
        self.assertIn("too large", error_message)

    def test_invalid_unicode_file(self):
        """Test that non-UTF8 files are rejected"""
        invalid_content = b"\xff\xfe\x00\x00"
        invalid_file = SimpleUploadedFile(
            "invalid.js", invalid_content, content_type="application/javascript"
        )

        with self.assertRaises(ValidationError) as context:
            validate_javascript_file(invalid_file)

        self.assertIn("not a valid JavaScript", str(context.exception))

    def test_empty_javascript_file(self):
        """Test that empty JavaScript file passes validation"""
        empty_js = ""
        js_file = SimpleUploadedFile(
            "empty.js", empty_js.encode("utf-8"), content_type="application/javascript"
        )

        result = validate_javascript_file(js_file)
        self.assertEqual(result, js_file)

    def test_validator_file_pointer_reset(self):
        """Test that validator resets file pointer after validation"""
        valid_js = 'console.log("test");'
        js_file = SimpleUploadedFile(
            "valid.js", valid_js.encode("utf-8"), content_type="application/javascript"
        )

        js_file.seek(0, 2)
        result = validate_javascript_file(js_file)

        self.assertEqual(js_file.tell(), 0)
        self.assertEqual(result, js_file)


class SiteConfigurationJavaScriptAdminTests(TestCase):
    """Test JavaScript functionality in SiteConfiguration admin"""

    def setUp(self):
        self.admin_instance = SiteConfigurationAdmin(SiteConfiguration, admin.site)
        self.site_config = SiteConfiguration.get_solo()
        self.valid_js_file = SimpleUploadedFile(
            "test.js", b'console.log("test");', content_type="application/javascript"
        )

    def tearDown(self):
        """Clean up uploaded files after tests"""
        if self.site_config.custom_javascript:
            self.site_config.custom_javascript.delete()

    @override_settings(ALLOW_CUSTOM_JS=True)
    def test_upload_javascript_without_confirmation_fails(self):
        """Test that uploading JavaScript without confirmation fails form validation"""
        config_dict = model_to_dict(self.site_config)

        # Remove file fields
        filter_keys = [
            field.name
            for field in SiteConfiguration._meta.fields
            if field.get_internal_type() in ("FileField", "AutoField")
            or field.name.endswith("_file")
        ]
        for key in filter_keys:
            config_dict.pop(key, None)

        config_dict.update(
            {
                "custom_javascript_confirmed": False,
            }
        )

        files = MultiValueDict({"custom_javascript": [self.valid_js_file]})
        form = SiteConfigurationAdminForm(
            data=config_dict, files=files, instance=self.site_config
        )

        self.assertFalse(form.is_valid())
        self.assertIn("custom_javascript_confirmed", form.errors)

    @override_settings(ALLOW_CUSTOM_JS=True)
    def test_upload_javascript_with_confirmation_succeeds(self):
        """Test that uploading JavaScript with confirmation succeeds"""
        config_dict = model_to_dict(self.site_config)

        # Remove file fields
        filter_keys = [
            field.name
            for field in SiteConfiguration._meta.fields
            if field.get_internal_type() in ("FileField", "AutoField")
            or field.name.endswith("_file")
        ]
        for key in filter_keys:
            config_dict.pop(key, None)

        # Ensure name field exists for form validation (only if missing)
        if "name" not in config_dict or not config_dict["name"]:
            config_dict["name"] = "Test Municipality"

        config_dict.update(
            {
                "custom_javascript_confirmed": True,
            }
        )

        files = MultiValueDict({"custom_javascript": [self.valid_js_file]})
        form = SiteConfigurationAdminForm(
            data=config_dict, files=files, instance=self.site_config
        )

        self.assertTrue(form.is_valid(), f"Form validation failed: {form.errors}")

    @override_settings(ALLOW_CUSTOM_JS=False)
    def test_custom_javascript_disabled_by_feature_flag(self):
        """Test that custom JavaScript upload fails when feature flag is disabled"""
        config_dict = model_to_dict(self.site_config)

        # Remove file fields
        filter_keys = [
            field.name
            for field in SiteConfiguration._meta.fields
            if field.get_internal_type() in ("FileField", "AutoField")
            or field.name.endswith("_file")
        ]
        for key in filter_keys:
            config_dict.pop(key, None)

        files = MultiValueDict({"custom_javascript": [self.valid_js_file]})
        form = SiteConfigurationAdminForm(data=config_dict, files=files)

        self.assertFalse(form.is_valid())
        self.assertIn("custom_javascript", form.errors)

        expected_error = _(
            "Custom JavaScript upload is disabled. Contact your system administrator to enable this feature by setting the ALLOW_CUSTOM_JS flag to true."
        )
        self.assertEqual(str(form.errors["custom_javascript"][0]), expected_error)

    @override_settings(ALLOW_CUSTOM_JS=True)
    def test_custom_javascript_enabled_shows_all_fields(self):
        """Test that all JavaScript fields appear when feature flag is enabled"""
        fieldsets = self.admin_instance.get_fieldsets(None)

        # Find Advanced display options fieldset
        advanced_fieldset = None
        for name, options in fieldsets:
            if "Advanced display options" in str(name) or "Geavanceerde" in str(name):
                advanced_fieldset = options
                break

        self.assertIsNotNone(
            advanced_fieldset, "Could not find Advanced display options fieldset"
        )

        # Should contain all JavaScript fields when enabled
        self.assertIn("custom_javascript_status", advanced_fieldset["fields"])
        self.assertIn("custom_javascript_confirmed", advanced_fieldset["fields"])
        self.assertIn("custom_javascript", advanced_fieldset["fields"])
        self.assertIn("custom_javascript_file_info", advanced_fieldset["fields"])

    @override_settings(ALLOW_CUSTOM_JS=False)
    def test_custom_javascript_disabled_shows_only_status_field(self):
        """Test that only status field appears when feature flag is disabled"""
        fieldsets = self.admin_instance.get_fieldsets(None)

        # Find Advanced display options fieldset
        advanced_fieldset = None
        for name, options in fieldsets:
            if "Advanced display options" in str(name) or "Geavanceerde" in str(name):
                advanced_fieldset = options
                break

        self.assertIsNotNone(
            advanced_fieldset, "Could not find Advanced display options fieldset"
        )

        # Should only contain status field when disabled
        self.assertIn("custom_javascript_status", advanced_fieldset["fields"])
        self.assertNotIn("custom_javascript_confirmed", advanced_fieldset["fields"])
        self.assertNotIn("custom_javascript", advanced_fieldset["fields"])
        self.assertNotIn("custom_javascript_file_info", advanced_fieldset["fields"])

    @override_settings(ALLOW_CUSTOM_JS=True)
    def test_custom_javascript_status_enabled_message(self):
        """Test that status shows enabled message when feature flag is true"""
        status_message = self.admin_instance.custom_javascript_status(self.site_config)

        self.assertIn("Custom JavaScript is enabled", status_message)
        self.assertIn('class="js-enabled"', status_message)

    @override_settings(ALLOW_CUSTOM_JS=False)
    def test_custom_javascript_status_disabled_message(self):
        """Test that status shows disabled message when feature flag is false"""
        status_message = self.admin_instance.custom_javascript_status(self.site_config)

        self.assertIn("Custom JavaScript is disabled", status_message)
        self.assertIn('class="js-disabled"', status_message)

    @override_settings(ALLOW_CUSTOM_JS=True)
    def test_javascript_file_info_display(self):
        """Test that file info shows name and size"""
        # Test with no file
        self.site_config.custom_javascript = None
        info = self.admin_instance.custom_javascript_file_info(self.site_config)
        self.assertEqual(info, "No file uploaded")

        # Test with file
        js_content = 'console.log("test");'  # This is 20 bytes
        js_file = SimpleUploadedFile(
            "test.js", js_content.encode("utf-8"), content_type="application/javascript"
        )
        self.site_config.custom_javascript = js_file
        self.site_config.save()

        info = self.admin_instance.custom_javascript_file_info(self.site_config)
        # Test exact expected message: filename and size
        self.assertEqual(info, "test.js: 0.0 KB")

    @override_settings(ALLOW_CUSTOM_JS=False)
    def test_custom_javascript_file_info_when_disabled(self):
        """Test file info when feature is disabled but file exists"""
        # Upload a file but feature is disabled
        js_content = 'console.log("disabled test");'
        js_file = SimpleUploadedFile(
            "disabled-test.js",
            js_content.encode("utf-8"),
            content_type="application/javascript",
        )
        self.site_config.custom_javascript = js_file
        self.site_config.save()

        info = self.admin_instance.custom_javascript_file_info(self.site_config)
        self.assertEqual(info, "File uploaded but feature is disabled")

    def test_javascript_field_upload_to_path(self):
        """Test that JavaScript files are uploaded to correct path"""
        field = self.site_config._meta.get_field("custom_javascript")
        self.assertEqual(field.upload_to, "custom_scripts/")

    @override_settings(ALLOW_CUSTOM_JS=True)
    def test_clear_javascript_file_with_additional_fields(self):
        """Test that JavaScript file can be cleared"""
        config = SiteConfiguration.get_solo()

        config.custom_javascript = self.valid_js_file
        config.custom_javascript_confirmed = True
        config.save()

        # Verify file exists
        self.assertTrue(config.custom_javascript)

        config_dict = model_to_dict(config)

        filter_keys = [
            field.name
            for field in SiteConfiguration._meta.fields
            if field.get_internal_type() in ("FileField", "AutoField")
            or field.name.endswith("_file")
        ]
        for key in filter_keys:
            config_dict.pop(key, None)

        # Ensure name field exists for form validation (only if missing)
        if "name" not in config_dict or not config_dict["name"]:
            config_dict["name"] = "Test Municipality"

        config_dict.update(
            {
                "custom_javascript": "",
                "custom_javascript-clear": True,
                "custom_javascript_confirmed": True,
            }
        )

        form = SiteConfigurationAdminForm(data=config_dict, instance=config)
        self.assertTrue(form.is_valid(), f"Form should be valid: {form.errors}")
        config = form.save()

        # File should be cleared
        self.assertFalse(config.custom_javascript)

    @override_settings(ALLOW_CUSTOM_JS=True)
    def test_javascript_file_info_filename_without_underscore(self):
        """Test file info display when filename has no underscore hash"""
        # Create a file with a simple name (no underscore hash)
        js_content = 'console.log("simple filename");'
        js_file = SimpleUploadedFile(
            "simple.js",
            js_content.encode("utf-8"),
            content_type="application/javascript",
        )
        self.site_config.custom_javascript = js_file
        self.site_config.save()

        info = self.admin_instance.custom_javascript_file_info(self.site_config)
        # Should use the original filename since there's no underscore
        self.assertEqual(info, "simple.js: 0.0 KB")

    @override_settings(ALLOW_CUSTOM_JS=True)
    def test_javascript_file_info_missing_from_storage(self):
        """Test file info when file exists in DB but missing from storage"""
        # Upload a file first
        js_content = 'console.log("test");'
        js_file = SimpleUploadedFile(
            "missing.js",
            js_content.encode("utf-8"),
            content_type="application/javascript",
        )
        self.site_config.custom_javascript = js_file
        self.site_config.save()

        with patch.object(
            self.site_config.custom_javascript.storage, "exists", return_value=False
        ):
            info = self.admin_instance.custom_javascript_file_info(self.site_config)
            self.assertEqual(info, "File missing from storage")

    @override_settings(ALLOW_CUSTOM_JS=True)
    def test_javascript_file_info_when_exception_is_raised(self):
        """Test file info when file exists in DB but missing from storage"""
        # Upload a file first
        js_content = 'console.log("test");'
        js_file = SimpleUploadedFile(
            "missing.js",
            js_content.encode("utf-8"),
            content_type="application/javascript",
        )
        self.site_config.custom_javascript = js_file
        self.site_config.save()

        with patch.object(
            self.site_config.custom_javascript.storage,
            "exists",
            side_effect=ValueError,
        ):
            info = self.admin_instance.custom_javascript_file_info(self.site_config)
            self.assertEqual(info, "Error accessing file")


@disable_admin_mfa()
class JavaScriptAdminRenderingTests(WebTest):
    """Test JavaScript admin page rendering in different scenarios"""

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(is_superuser=True, is_staff=True)

    @override_settings(ALLOW_CUSTOM_JS=True)
    def test_admin_renders_with_javascript_enabled(self):
        """Test that admin page renders correctly when JavaScript is enabled"""
        response = self.app.get(
            reverse("admin:configurations_siteconfiguration_change"), user=self.user
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="custom_javascript"')
        self.assertContains(response, "custom_javascript_confirmed")
        self.assertContains(response, "Custom JavaScript is enabled")

    @override_settings(ALLOW_CUSTOM_JS=False)
    def test_admin_renders_with_javascript_disabled(self):
        """Test that admin page renders correctly when JavaScript is disabled"""
        response = self.app.get(
            reverse("admin:configurations_siteconfiguration_change"), user=self.user
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="custom_javascript"')
        self.assertNotContains(response, "custom_javascript_confirmed")
        self.assertContains(response, "Custom JavaScript is disabled")


@disable_admin_mfa()
class AdminPermissionTest(WebTest):
    def setUp(self):
        self.superuser = UserFactory(is_superuser=True, is_staff=True)
        self.beheerder = UserFactory(is_staff=True)

        siteconfig_ct = ContentType.objects.get_for_model(SiteConfiguration)
        perm_warning, _ = Permission.objects.get_or_create(
            codename="siteconfig_fieldset_warning_banner",
            name="Can edit warning banner",
            content_type=siteconfig_ct,
        )
        self.beheerder.user_permissions.add(perm_warning)

    def test_admin_change_restricted(self):
        """
        Test that users with restricted permissions cannot modify fields they don't have
        access to, even when submitting a POST request with those fields.
        """
        config = SiteConfiguration.get_solo()
        config.warning_banner_text = "Old warning banner text"
        config.enable_crawler_indexing = False
        config.save()

        form = self.app.get(
            reverse("admin:configurations_siteconfiguration_change"),
            user=self.beheerder,
        ).forms["siteconfiguration_form"]

        # Modify authorized field
        form["warning_banner_text"] = "Warning banner text changed"

        # Attempt to modify unauthorized field
        form.fields["enable_crawler_indexing"] = True

        response = form.submit()

        self.assertEqual(response.status_code, 302)

        config.refresh_from_db()

        # Authorized field should be changed
        self.assertEqual(config.warning_banner_text, "Warning banner text changed")

        # Unauthorized field should not be changed
        self.assertEqual(config.enable_crawler_indexing, False)

    def test_admin_form_access_restricted(self):
        """Test that users with restricted permissions do not see restricted fields"""

        form = self.app.get(
            reverse("admin:configurations_siteconfiguration_change"),
            user=self.beheerder,
        ).forms["siteconfiguration_form"]

        # check that we can't access restricted fields, one for each fieldset
        restricted_fields = [
            "enable_crawler_indexing",
            "primary_color",
            "email_logo",
            "login_text",
            "home_help_text",
            "include_cms_pages_in_search_index",
            "enable_notification_channel_choice",
            "openid_connect_logo",
            "eherkenning_enabled",
            "gtm_code",
            "cookie_info_text",
            "kcm_survey_link_text",
            "hide_categories_from_anonymous_users",
            "theme_stylesheet",
            "display_social",
            "contactmoment_contact_form_enabled",
        ]

        # Verify that restricted fields are not accessible in the form
        for field in restricted_fields:
            with self.assertRaises(AssertionError):
                form[field]

        # Verify that the allowed field is accessible
        self.assertIsNotNone(form["warning_banner_text"])

    def test_admin_form_superuser_access_full(self):
        """Test that superusers can see restricted fields"""

        form = self.app.get(
            reverse("admin:configurations_siteconfiguration_change"),
            user=self.superuser,
        ).forms["siteconfiguration_form"]

        # Fields that should be accessible to superusers (one from each fieldset)
        all_fields = [
            "enable_crawler_indexing",
            "primary_color",
            "email_logo",
            "login_text",
            "home_help_text",
            "include_cms_pages_in_search_index",
            "enable_notification_channel_choice",
            "openid_connect_logo",
            "eherkenning_enabled",
            "gtm_code",
            "cookie_info_text",
            "kcm_survey_link_text",
            "hide_categories_from_anonymous_users",
            "theme_stylesheet",
            "display_social",
            "contactmoment_contact_form_enabled",
            "warning_banner_text",
        ]

        for field in all_fields:
            try:
                form[field]
            except AssertionError:
                self.fail(f"Superuser could not access field: {field}")
