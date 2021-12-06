from django import http
from django.template import TemplateDoesNotExist, loader
from django.views.decorators.csrf import requires_csrf_token
from django.views.defaults import ERROR_500_TEMPLATE_NAME

from view_breadcrumbs import DetailBreadcrumbMixin


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
