from unittest.mock import patch

from django.test import override_settings, tag
from django.utils.translation import gettext

import clamd
from cms.models.static_placeholder import StaticPlaceholder
from playwright.sync_api import expect

from open_inwoner.accounts.tests.factories import DigidUserFactory
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.plans.tests.factories import PlanFactory
from open_inwoner.utils.tests.playwright import PlaywrightSyncLiveServerTestCase


@tag("e2e")
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class PlansHTMXTest(PlaywrightSyncLiveServerTestCase):
    uploaded_bytes = b"fake pdf"
    uploaded_filename = "upload_test.pdf"

    def setUp(self):
        super().setUp()

        self.user = DigidUserFactory(bsn="900222086")
        self.user_login_state = self.get_user_bsn_login_state(self.user)

        self.plan_factory = PlanFactory

        # Ensure only one StaticPlaceholder exists per slot/code to avoid MultipleObjectsReturned in CI
        for code in ["footer_left", "footer_center", "footer_right"]:
            placeholders = StaticPlaceholder.objects.filter(code=code)
            if placeholders.count() > 1:
                placeholders.exclude(pk=placeholders.first().pk).delete()

        # Disable cookie banner
        self.config = SiteConfiguration.get_solo()
        self.config.cookie_info_text = ""
        self.config.save()

        self.context = self.browser.new_context(
            base_url=self.live_server_url,
            storage_state=self.user_login_state,
        )

    def tearDown(self) -> None:
        self.context.close()
        return super().tearDown()

    def test_plan_file_upload_e2e(self):
        """Upload a file via the Plan detail page and confirm it's displayed and downloadable."""

        plan = self.plan_factory(created_by=self.user)
        plan.plan_contacts.add(self.user)

        page = self.context.new_page()

        # Go to plan detail page
        page.goto(
            self.live_reverse("collaborate:plan_detail", kwargs={"uuid": plan.uuid})
        )

        # Confirm URL loaded
        expect(page).to_have_url(
            self.live_reverse("collaborate:plan_detail", kwargs={"uuid": plan.uuid})
        )

        # Wait for outer HTMX container to be available
        form_upload = page.locator("#form_upload")
        expect(form_upload).to_be_visible(timeout=10_000)

        # Scroll to reveal the form (triggers hx-trigger="revealed")
        page.evaluate("document.querySelector('#form_upload')?.scrollIntoView()")
        page.wait_for_load_state("networkidle")  # Wait for JS/XHR

        # Wait for HTMX to fully swap in #document-upload (with retry loop for CI stability)
        upload_form = page.locator("#document-upload")
        for attempt in range(5):
            if upload_form.count() > 0:
                break
            page.wait_for_timeout(2000)
        else:
            raise Exception("HTMX swap failed: #document-upload not found")

        expect(upload_form).to_be_visible(timeout=10_000)

        # Upload document
        file_input = upload_form.get_by_label(
            gettext("Sleep of selecteer bestand"), exact=True
        )
        file_input.set_input_files(
            {
                "name": self.uploaded_filename,
                "mimeType": "application/pdf",
                "buffer": self.uploaded_bytes,
            }
        )

        # Submit the form
        submit_button = upload_form.get_by_role(
            "button", name=gettext("Upload document")
        )
        expect(submit_button).to_be_visible()
        submit_button.click()

        # Ensure uploaded document appears
        plan_file_container = page.locator(".plan__file")
        files = plan_file_container.locator(".file")
        expect(files).to_have_count(1)

        # Download the uploaded file
        download_link = page.locator(".plan__file a.file__download")
        expect(download_link).to_be_visible(timeout=10_000)

        with page.expect_download() as download_info:
            download_link.click()

        download = download_info.value
        with open(download.path(), "rb") as f:
            assert f.read() == self.uploaded_bytes

    def _submit_upload_form(self, page, plan, filename, mime_type, file_bytes):
        """Helper: navigate to plan detail, wait for HTMX upload form, upload a file."""
        page.goto(
            self.live_reverse("collaborate:plan_detail", kwargs={"uuid": plan.uuid})
        )
        expect(page).to_have_url(
            self.live_reverse("collaborate:plan_detail", kwargs={"uuid": plan.uuid})
        )

        form_upload = page.locator("#form_upload")
        expect(form_upload).to_be_visible(timeout=10_000)
        page.evaluate("document.querySelector('#form_upload')?.scrollIntoView()")
        page.wait_for_load_state("networkidle")

        upload_form = page.locator("#document-upload")
        for _ in range(5):
            if upload_form.count() > 0:
                break
            page.wait_for_timeout(2000)
        else:
            raise Exception("HTMX swap failed: #document-upload not found")

        expect(upload_form).to_be_visible(timeout=10_000)

        file_input = upload_form.get_by_label(
            gettext("Sleep of selecteer bestand"), exact=True
        )
        file_input.set_input_files(
            {"name": filename, "mimeType": mime_type, "buffer": file_bytes}
        )

        submit_button = upload_form.get_by_role(
            "button", name=gettext("Upload document")
        )
        expect(submit_button).to_be_visible()
        submit_button.click()

    def test_plan_file_upload_virus_scan_disabled_allows_upload(self):
        plan = self.plan_factory(created_by=self.user)
        plan.plan_contacts.add(self.user)

        # Virus scan is disabled by default.
        assert not self.config.enable_virus_scan

        page = self.context.new_page()
        self._submit_upload_form(
            page,
            plan,
            filename="eicar_test.txt",
            mime_type="text/plain",
            # clamd.EICAR is the official EICAR antivirus test string.
            file_bytes=clamd.EICAR,
        )

        # The file should have been accepted and appear in the plan's file list.
        plan_file_container = page.locator(".plan__file")
        files = plan_file_container.locator("file-nlds")
        expect(files).to_have_count(1)

    def test_plan_file_upload_virus_found_shows_error(self):
        plan = self.plan_factory(created_by=self.user)
        plan.plan_contacts.add(self.user)

        self.config.enable_virus_scan = True
        self.config.clamav_host = "clamav"
        self.config.clamav_port = 3310
        self.config.save()

        # Patch clamd at the source used by the validator so no daemon is needed.
        with patch(
            "open_inwoner.utils.validators.clamd.ClamdNetworkSocket"
        ) as mock_clamd_cls:
            mock_scanner = mock_clamd_cls.return_value
            mock_scanner.instream.return_value = {
                "stream": ("FOUND", "Eicar-Test-Signature")
            }

            page = self.context.new_page()
            self._submit_upload_form(
                page,
                plan,
                filename="eicar_test.txt",
                mime_type="text/plain",
                file_bytes=clamd.EICAR,
            )

        # The file must NOT have been saved — no plan files expected.
        plan_file_container = page.locator(".plan__file")
        files = plan_file_container.locator("file-nlds")
        expect(files).to_have_count(0)

        # An error message about the virus scan should be visible.
        error = page.locator(".notification--error, .messages .error, [role='alert']")
        expect(error).to_be_visible(timeout=5_000)
        expect(error).to_contain_text("virus", ignore_case=True)
