import re
from urllib.parse import parse_qs, urlparse

from django.conf import settings
from django.test import tag
from django.urls import reverse

from cms.models import CMSPlugin
from maykin_common.csp.constants import CSPDirective
from maykin_common.csp.models import CSPSetting
from playwright.sync_api import FrameLocator, Page as BrowserPage, expect

from open_inwoner.cms.tests.playwright import CMSAdminTests


@tag("e2e")
class HomepageEditingTests(CMSAdminTests):
    """
    An editor building the homepage from scratch, through the admin.
    """

    def setUp(self):
        super().setUp()

        # like any installation using the video plugin, which embeds Vimeo
        CSPSetting.objects.create(
            directive=CSPDirective.FRAME_SRC, value="https://player.vimeo.com"
        )

        self.page = self.get_context().new_page()
        self.log_in_to_admin(self.page)
        self.add_page(self.page, "Home")

    def get_allowed_plugins(self, slot: str) -> list[str]:
        return sorted(settings.CMS_PLACEHOLDER_CONF[slot]["plugins"])

    def fill_plugin_form(self, form: FrameLocator, plugin_type: str):
        """
        Fill in what an editor has to, for the plugin to be saved.
        """
        match plugin_type:
            case "TextPlugin":
                self.fill_prosemirror(form, "body", "Welkom op de homepage")
            case "BannerTextPlugin":
                form.locator("input[name='title']").fill("Welkom")
            case "BannerImagePlugin":
                self.drop_image(form, "image")
            case "PicturePlugin":
                self.drop_image(form, "picture")
            case "VideoPlayerPlugin":
                self.add_video(self.page, form)

    def add_video(self, page: BrowserPage, form: FrameLocator):
        """
        Add a video to the catalog, from the plugin form's video field.
        """
        with page.expect_popup() as popup_info:
            form.locator("#add_id_video").click()
        popup = popup_info.value

        popup.locator("input[name='link_id']").fill("123456789")
        with popup.expect_event("close"):
            popup.locator("input[name='_save']").click()

        expect(form.locator("select[name='video']")).not_to_have_value("")

    def test_new_homepage_can_be_published(self):
        self.open_in_edit_mode(self.page)
        self.publish(self.page)

        visitor = self.get_context().new_page()
        response = visitor.goto(self.live_url("/"))

        self.assertEqual(response.status, 200)
        expect(visitor).to_have_title(re.compile(r"^Home\b"))

    # regression test for the global `CMS_PLACEHOLDER_CONF[None]["plugins"]`
    # restricting the picker of every placeholder since django-cms 5
    def test_plugin_picker_offers_all_allowed_plugins(self):
        self.open_in_edit_mode(self.page)
        self.switch_to_structure_mode(self.page)

        draft = self.get_homepage_draft()
        slots = self.get_placeholder_slots(draft)
        self.assertNotEqual(slots, [])

        add_plugin_path = reverse("admin:cms_placeholder_add_plugin")

        for slot in slots:
            allowed_plugins = self.get_allowed_plugins(slot)
            dragarea = self.get_dragarea(self.page, self.get_placeholder(draft, slot))
            add_button = dragarea.locator(".cms-dragbar .cms-submenu-add")

            with self.subTest(slot=slot):
                if len(allowed_plugins) == 1:
                    # with a single choice, CMS skips the picker and goes straight
                    # to the add form of that plugin
                    with self.page.expect_request(
                        lambda request: add_plugin_path in request.url
                    ) as request_info:
                        add_button.click()
                    query = parse_qs(urlparse(request_info.value.url).query)
                    offered_plugins = query["plugin_type"]
                else:
                    add_button.click()
                    picker = self.get_plugin_picker(self.page)
                    expect(picker).to_be_visible()
                    offered_plugins = sorted(
                        picker.locator(
                            ".cms-submenu-item:not(.cms-submenu-item-title) a"
                        ).evaluate_all(
                            "links => links.map(a => a.getAttribute('href'))"
                        )
                    )

                # close the modal before asserting, so a failure doesn't block
                # the next placeholder's "+" button
                self.close_modal(self.page)

                self.assertEqual(offered_plugins, allowed_plugins)

    def test_all_allowed_plugins_can_be_added_and_saved(self):
        self.open_in_edit_mode(self.page)
        self.switch_to_structure_mode(self.page)

        draft = self.get_homepage_draft()
        slots = self.get_placeholder_slots(draft)
        self.assertNotEqual(slots, [])

        for slot in slots:
            allowed_plugins = self.get_allowed_plugins(slot)
            placeholder = self.get_placeholder(draft, slot)
            dragarea = self.get_dragarea(self.page, placeholder)

            for plugin_type in allowed_plugins:
                with self.subTest(slot=slot, plugin_type=plugin_type):
                    form = self.open_plugin_form(
                        self.page,
                        dragarea,
                        plugin_type,
                        picker=len(allowed_plugins) > 1,
                    )
                    self.fill_plugin_form(form, plugin_type)
                    self.save_plugin_form(self.page, form)

                    plugin = CMSPlugin.objects.get(
                        placeholder=placeholder, plugin_type=plugin_type
                    )
                    expect(
                        dragarea.locator(f".cms-draggable-{plugin.pk}")
                    ).to_be_attached()

        added_plugins = {
            slot: sorted(
                CMSPlugin.objects.filter(
                    placeholder=self.get_placeholder(draft, slot)
                ).values_list("plugin_type", flat=True)
            )
            for slot in slots
        }
        self.assertEqual(
            added_plugins, {slot: self.get_allowed_plugins(slot) for slot in slots}
        )

        # the page, with all of its plugins, renders for visitors
        self.publish(self.page)
        visitor = self.get_context().new_page()
        response = visitor.goto(self.live_url("/"))
        self.assertEqual(response.status, 200)
