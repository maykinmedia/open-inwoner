from django.http import HttpResponse, HttpResponseBadRequest
from django.views import View
from django.views.generic.edit import ModelFormMixin

from open_inwoner.components.utils import RenderableTag
from open_inwoner.htmx.mixins import RequiresHtmxMixin


class HtmxTemplateTagModelFormView(RequiresHtmxMixin, ModelFormMixin, View):
    """
    ModelFormMixin-based view to support htmx by handling a hx-post with a ModelForm,
    and respond with the output of a template tag (eg: a partial without extra templates)

    Uses the standard ModelView/FormView-related methods and class attributes
    - model, queryset, get_queryset() etc
    - form, form_class, fields, get_form_kwargs() etc

    Requires the request to be a POST from htmx

    Returns either new HTML or HTTP Bad Request on invalid form

    Note:
    - this is an experimental exploration on how to do htmx
    - initial use-case is a button that updates a field on a model (like a status)
    """

    template_tag: RenderableTag = None

    def get_template_tag_args(self, context: dict) -> dict:
        """
        override me and return a dict with the arguments of the template tag
        """
        return {
            "request": self.request,
        }

    def form_valid(self, form):
        self.object = form.save()
        return self.get_response()

    def form_invalid(self, form):
        return HttpResponseBadRequest("invalid")

    def render_template_tag(self) -> str:
        context = self.get_context_data()
        template_tag = self.get_template_tag(context)
        tag_args = self.get_template_tag_args(context)
        return template_tag.render(tag_args)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_template_tag(self, context: dict) -> RenderableTag:
        if not self.template_tag:
            raise ValueError("define .template_tag or override .get_template_tag()")
        return self.template_tag

    def get_response(self):
        return HttpResponse(self.render_template_tag(), content_type="text/html")
