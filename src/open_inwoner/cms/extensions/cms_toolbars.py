from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

from cms.extensions.toolbar import ExtensionToolbar
from cms.models import PageContent
from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool

from .models import CommonExtension

# the CMS endpoints that render an object in edit or preview mode
CMS_RENDER_OBJECT_ENDPOINTS = (
    "cms_placeholder_render_object_edit",
    "cms_placeholder_render_object_preview",
)


@toolbar_pool.register
class CommonExtensionToolbar(ExtensionToolbar):
    model = CommonExtension

    def populate(self):
        current_page_menu = self._setup_extension_toolbar()
        if current_page_menu:
            page_extension, url = self.get_page_extension_admin()
            if url:
                current_page_menu.add_modal_item(
                    _("Pagina opties"),
                    url=url,
                    disabled=(not self.toolbar.edit_mode_active),
                    position=2,
                )


@toolbar_pool.register
class PageContentObjectToolbar(CMSToolbar):
    """
    Set the CMS page's content as the toolbar object when no view has set one.

    Without an object, the toolbar has no edit button on the live page, and no
    structure mode switcher or publish button in edit mode. For regular CMS
    pages, the CMS sets the object itself, so this does nothing. The CMS leaves
    it to the views of an apphook page, and ours don't set one.

    Which content is set depends on how the page is rendered:

    - on the live page, the published content, as the CMS sets for regular pages
    - on the CMS edit and preview endpoints, the version being edited or
      previewed, which needn't be the latest. For an apphook page, these
      endpoints replace the toolbar before rendering the apphook's view, so the
      object can't be set any earlier in the request (e.g. by a middleware).

    This runs when the toolbar is rendered for staff, before the page body and
    before the toolbars add their buttons in `post_template_populate`. Visitors
    don't need an object: placeholders fall back to the published content.
    """

    def populate(self):
        if self.toolbar.obj is not None:
            return

        page_content = self.get_rendered_page_content()
        if page_content:
            self.toolbar.set_object(page_content)

    def get_rendered_page_content(self) -> PageContent | None:
        match = self.request.resolver_match
        if match is not None and match.url_name in CMS_RENDER_OBJECT_ENDPOINTS:
            content_type_id, object_id = match.args
            content_type = ContentType.objects.get_for_id(content_type_id)
            if content_type.model_class() is not PageContent:
                return None
            return PageContent.admin_manager.filter(pk=object_id).first()

        # page is a lazy object, so `is None` doesn't work
        page = self.request.current_page
        if not page:
            return None
        return page.get_content_obj(self.current_lang, fallback=False) or None
