from django import http
from django.core.exceptions import PermissionDenied
from django.template import TemplateDoesNotExist, loader
from django.views import View
from django.views.decorators.csrf import requires_csrf_token
from django.views.defaults import ERROR_500_TEMPLATE_NAME

from django_sendfile import sendfile

from .storage import private_storage


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


class DownloadExportView(View):
    def get(self, request, path):
        if request.user.is_authenticated:
            fs_path = private_storage.path(path)
            return sendfile(request, fs_path, attachment=True)

        raise PermissionDenied
