import base64
import io
import re

from django.test import override_settings
from django.utils import translation

from cms.models import Page, PageContent, Placeholder
from cms.utils.placeholder import get_declared_placeholders_for_obj
from maykin_2fa.test import disable_admin_mfa
from PIL import Image
from playwright.sync_api import FrameLocator, Locator, Page as BrowserPage, expect

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.cms.tests import cms_tools
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.utils.test import ClearCachesMixin
from open_inwoner.utils.tests.playwright import PlaywrightSyncLiveServerTestCase

# Dispatches the events of dragging `fileName` onto `dropzone` (filer's image
# widgets only accept drops, not clicks).
DROP_FILE_JS = """
(dropzone, {fileName, mimeType, base64Content}) => {
    const bytes = Uint8Array.from(atob(base64Content), char => char.charCodeAt(0));
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(new File([bytes], fileName, {type: mimeType}));
    for (const type of ["dragenter", "dragover", "drop"]) {
        dropzone.dispatchEvent(
            new DragEvent(type, {dataTransfer, bubbles: true, cancelable: true})
        );
    }
}
"""


@disable_admin_mfa()
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class CMSAdminTests(ClearCachesMixin, PlaywrightSyncLiveServerTestCase):
    """
    Base class for browser tests that use the CMS the way an editor does: through
    the admin, the toolbar and the structure board.
    """

    # the admin index groups editors navigate by (not loaded on migrate in CI)
    fixtures = ["django-admin-index"]

    def setUp(self):
        super().setUp()
        # see the helper's docstring: without this the CMS toolbar 500s
        cms_tools.reset_versionables_content_type_cache()

        self.user = UserFactory(is_staff=True, is_superuser=True)

        # avoid the cookie banner overlapping/intercepting clicks
        config = SiteConfiguration.get_solo()
        config.cookie_info_text = ""
        config.save()

    # -- Admin ----------------------------------------------------------------

    def log_in_to_admin(self, page: BrowserPage):
        page.goto(self.live_reverse("admin:login"))
        page.locator("input[name='auth-username']").fill(self.user.email)
        page.locator("input[name='auth-password']").fill("secret")
        page.locator("input[name='auth-password']").press("Enter")
        page.wait_for_url(self.live_reverse("admin:index"))

    def add_page(self, page: BrowserPage, title: str):
        """
        Add a page from the admin index, ending up in the page tree.

        The first page of a site becomes its homepage.
        """
        cms_group = page.locator("table").filter(
            has=page.locator("caption", has_text="CMS")
        )
        cms_group.locator("a.addlink").click()

        page.locator("input[name='title']").fill(title)
        page.locator("input[name='_save']").click()

    # -- Toolbar ----------------------------------------------------------------

    def open_in_edit_mode(self, page: BrowserPage):
        """
        Open the (only) page in the page tree in edit mode, creating a draft if
        it's published.
        """
        page.locator(".js-cms-pagetree-page-view").click()
        page.locator(".cms-toolbar .cms-versioning-js-edit-btn").click()
        page.wait_for_url("**/edit/**")

    def switch_to_structure_mode(self, page: BrowserPage):
        page.locator(".cms-toolbar-item-cms-mode-switcher a").click()
        expect(page.locator(".cms-structure")).to_be_visible()

    def publish(self, page: BrowserPage):
        page.locator(".cms-toolbar .cms-versioning-js-publish-btn").click()
        page.wait_for_url(lambda url: "/edit/" not in url)

    # -- Structure board --------------------------------------------------------

    def get_homepage_draft(self) -> PageContent:
        return Page.objects.get(is_home=True).get_admin_content("nl")

    def get_placeholder_slots(self, content: PageContent) -> list[str]:
        return [
            declared.slot for declared in get_declared_placeholders_for_obj(content)
        ]

    def get_placeholder(self, content: PageContent, slot: str) -> Placeholder:
        return Placeholder.objects.get_for_obj(content).get(slot=slot)

    def get_dragarea(self, page: BrowserPage, placeholder: Placeholder) -> Locator:
        """
        Find a placeholder in the structure board by the label editors see.
        """
        with translation.override("nl"):
            label = placeholder.get_label()

        return page.locator(".cms-dragarea").filter(
            has=page.locator(".cms-dragbar").get_by_title(label, exact=True)
        )

    def get_plugin_picker(self, page: BrowserPage) -> Locator:
        return page.locator(".cms-modal .cms-plugin-picker")

    def open_plugin_form(
        self, page: BrowserPage, dragarea: Locator, plugin_type: str, *, picker=True
    ) -> FrameLocator:
        """
        Click the placeholder's "+" and open the add form of `plugin_type`.

        Pass `picker=False` for placeholders that allow a single plugin: CMS then
        skips the picker and opens its form straight away.
        """
        dragarea.locator(".cms-dragbar .cms-submenu-add").click()

        if picker:
            self.get_plugin_picker(page).locator(
                f".cms-submenu-item a[href='{plugin_type}']"
            ).click()

        form = page.frame_locator(".cms-modal-frame iframe")
        expect(form.locator("#content form")).to_be_attached()
        return form

    def save_plugin_form(self, page: BrowserPage, form: FrameLocator):
        page.locator(".cms-modal-buttons .cms-btn-action").first.click()

        modal = page.locator(".cms-modal")
        try:
            expect(modal).to_be_hidden()
        except AssertionError:
            errors = form.locator(".errornote, .errorlist").all_inner_texts()
            # so the failure doesn't block the next plugin's "+" button
            self.close_modal(page)
            self.fail(f"Saving the plugin failed: {errors}")

    def close_modal(self, page: BrowserPage):
        modal = page.locator(".cms-modal")
        modal.locator(".cms-modal-close").click()
        expect(modal).to_be_hidden()

    # -- Form widgets ---------------------------------------------------------

    def fill_prosemirror(self, form: FrameLocator, field_name: str, text: str):
        form.locator(f"#id_{field_name}-editor [contenteditable='true']").fill(text)

    def drop_image(self, form: FrameLocator, field_name: str):
        """
        Upload an image to a filer image field, by dropping it onto the widget.
        """
        image = io.BytesIO()
        Image.new("RGB", (16, 16), "teal").save(image, format="PNG")

        hidden_input = form.locator(f"input[name='{field_name}']")
        dropzone = form.locator(".js-filer-dropzone").filter(has=hidden_input)
        dropzone.evaluate(
            DROP_FILE_JS,
            {
                "fileName": f"{field_name}.png",
                "mimeType": "image/png",
                "base64Content": base64.b64encode(image.getvalue()).decode(),
            },
        )
        # filer sets the uploaded file's pk once the upload succeeds
        expect(hidden_input).to_have_value(re.compile(r"^\d+$"))
