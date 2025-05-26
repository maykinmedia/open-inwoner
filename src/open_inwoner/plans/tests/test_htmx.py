from django.test import override_settings, tag
from django.utils.translation import gettext as _

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

        # Disable cookie banner
        self.config = SiteConfiguration.get_solo()
        self.config.cookie_info_text = ""
        self.config.save()

    def test_plan_file_upload_e2e(self):
        """Upload a file via the Plan detail page and confirm it's displayed and downloadable."""

        plan = self.plan_factory(created_by=self.user)
        plan.plan_contacts.add(self.user)

        context = self.browser.new_context(
            base_url=self.live_server_url,
            storage_state=self.user_login_state,
            record_video_dir="videos/",
        )
        page = context.new_page()

        # Go to plan detail page
        page.goto(
            self.live_reverse("collaborate:plan_detail", kwargs={"uuid": plan.uuid})
        )

        # Confirm URL loaded
        expect(page).to_have_url(
            self.live_reverse("collaborate:plan_detail", kwargs={"uuid": plan.uuid})
        )

        # Wait for outer HTMX container to be available
        page.wait_for_selector("#form_upload", timeout=10_000)

        # Scroll to reveal the form (triggers hx-trigger="revealed")
        page.evaluate("document.querySelector('#form_upload')?.scrollIntoView()")
        page.wait_for_timeout(1000)  # give HTMX some time to fire

        # Wait for HTMX to fully swap in #document-upload
        page.wait_for_function(
            "document.querySelector('#document-upload') !== null", timeout=20_000
        )
        upload_form = page.locator("#document-upload")

        # Upload document
        file_input = upload_form.get_by_label(
            _("Sleep of selecteer bestand"), exact=True
        )
        file_input.set_input_files(
            {
                "name": self.uploaded_filename,
                "mimeType": "application/pdf",
                "buffer": self.uploaded_bytes,
            }
        )

        # Submit the form
        submit_button = upload_form.get_by_role("button", name=_("Upload document"))
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
