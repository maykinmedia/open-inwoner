from django.http import HttpResponseRedirect
from django.utils.translation import get_language

from cms.models import PageContent
from cms.toolbar.utils import get_toolbar_from_request
from djangocms_versioning.constants import DRAFT, PUBLISHED

from open_inwoner.configurations.models import SiteConfiguration


class AnonymousHomePageRedirectMiddleware:
    """
    Redirect the user from home page to a desired page provided via the
    SiteConfiguration singleton. The validity of the path or url is being
    checked in the admin form.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if not request.user.is_authenticated and (
            request.path == "/" or request.path == "/nl/"
        ):
            config = SiteConfiguration.get_solo()
            if config.redirect_to:
                return HttpResponseRedirect(config.redirect_to)

        return response


class DropToolbarMiddleware:
    """
    Hide the django-cms toolbar if the staff user is not 2FA verified

    Needed because only the admin has forced OTP,
      so the inline editing iframes of django-cms could be accessed but then show a confusing 2FA flow
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        toolbar = get_toolbar_from_request(request)

        if self.force_disable_toolbar(request):
            request.session["cms_edit"] = False
            request.session["cms_preview"] = False
            request.session["cms_toolbar_disabled"] = True
            toolbar.show_toolbar = False
        else:
            request.session.pop("cms_toolbar_disabled", None)

        # VersionContentRenderer.render_obj_placeholder (djangocms_versioning) needs
        # toolbar.get_object() to return a PageContent for any view that uses
        # {% placeholder %} tags — including apphook views where cms/views.py never
        # runs and therefore never calls toolbar.set_object().
        page = getattr(request, "current_page", None)
        if page:
            language = get_language()
            edit_or_preview = toolbar.edit_mode_active or toolbar.preview_mode_active
            if edit_or_preview:
                # In edit/preview mode prefer the DRAFT version; fall back to PUBLISHED
                # so the editor sees the content they're working on.
                page_content = (
                    PageContent._original_manager.filter(
                        page=page, language=language, versions__state=DRAFT
                    ).first()
                    or PageContent._original_manager.filter(
                        page=page, language=language, versions__state=PUBLISHED
                    ).first()
                )
            else:
                page_content = PageContent._original_manager.filter(
                    page=page, language=language, versions__state=PUBLISHED
                ).first()
            if page_content:
                toolbar.set_object(page_content)

        response = self.get_response(request)
        return response

    def force_disable_toolbar(self, request):
        return (not request.user.is_staff) or (not request.user.is_verified())
