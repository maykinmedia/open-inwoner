from django import http
from django.contrib.auth.mixins import AccessMixin
from django.template import TemplateDoesNotExist, loader
from django.views.decorators.csrf import requires_csrf_token
from django.views.defaults import ERROR_500_TEMPLATE_NAME

from view_breadcrumbs import DetailBreadcrumbMixin

from .logentry import addition, change, deletion, system_action, user_action


class CommonPageMixin:
    @property
    def page_title(self):
        page_title = ""
        try:
            # hook into breadcrumbs
            page_title = self.crumbs[-1][0]
        except (AttributeError, IndexError):
            pass

        return page_title

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        return context


class CustomDetailBreadcrumbMixin(DetailBreadcrumbMixin):
    no_list = False

    def get_breadcrumb_name(self):
        return str(self.object)

    @property
    def crumbs(self):
        if self.no_list:
            return [
                (
                    self.get_breadcrumb_name(),
                    self.detail_view_url,
                ),
            ]
        return super(DetailBreadcrumbMixin, self).crumbs + [
            (
                self.get_breadcrumb_name(),
                self.detail_view_url,
            ),
        ]


class LoginMaybeRequiredMixin(AccessMixin):
    """
    Conditional access control on a per-view basis

    Access to the view is restricted to authenticated users if
    `self.display_restricted` is `True`, which must be defined on
    the view inheriting from this Mixin.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated and self.display_restricted:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


@requires_csrf_token
def server_error(request, template_name=ERROR_500_TEMPLATE_NAME):
    """
    500 error handler.

    Templates: :template:`500.html`
    Context: None
    """
    try:
        template = loader.get_template(template_name)
    except TemplateDoesNotExist:
        if template_name != ERROR_500_TEMPLATE_NAME:
            # Reraise if it's a missing custom template.
            raise
        return http.HttpResponseServerError(
            "<h1>Server Error (500)</h1>", content_type="text/html"
        )
    context = {"request": request}
    return http.HttpResponseServerError(template.render(context))


class LogMixin(object):
    """
    CBV mixin that adds simple wrappers to logging functions
    """

    def log_addition(self, instance, message=""):
        """
        Log that an object has been successfully added.
        """
        addition(self.request, instance, message)

    def log_change(self, instance, message):
        """
        Log that an object has been successfully changed.
        """
        change(self.request, instance, message)

    def log_deletion(self, instance, message):
        """
        Log that an object will be deleted.
        """
        deletion(self.request, instance, message)

    def log_user_action(self, instance, message):
        """
        Log that the current user has done something interesting.
        """
        user_action(self.request, instance, message)

    def log_system_action(self, message, instance=None, user=None):
        """
        Log system events not related to a specific user.
        """
        system_action(message, content_object=instance, user=user)
