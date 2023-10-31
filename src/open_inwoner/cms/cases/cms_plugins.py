from django.core.exceptions import BadRequest
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

# TODO: import `preprocess_data` after merge of PR 804
from open_inwoner.openzaak.cases import fetch_cases
from open_inwoner.openzaak.formapi import fetch_open_submissions

from ..utils.auth import check_user_access_rights, check_user_auth
from ..utils.plugin_mixins import CMSActiveAppMixin


# TODO: refactor after merge of PR 804
@plugin_pool.register_plugin
class CasesPlugin(CMSActiveAppMixin, CMSPluginBase):
    module = _("Openzaak")
    name = _("Cases Plugin")
    render_template = "cms/cases/cases_plugin.html"
    app_hook = "CasesApphook"
    cache = False

    limit = 4

    def render(self, context, instance, placeholder):
        request = context["request"]
        user = request.user
        if check_user_auth(user, digid_required=True):
            context["hxget"] = reverse("cases:cases_plugin_content")
        return context

    @classmethod
    def render_htmx_content(cls, request):
        user = request.user
        context = dict()
        context["page_title"] = "Page title"
        context["title_text"] = "Title text"

        if not check_user_auth(user, digid_required=True):
            return context

        raw_cases = [case for case in fetch_cases(user.bsn) if not case.einddatum]

        if not all(check_user_access_rights(user, case.url) for case in raw_cases):
            return context

        # TODO
        # preprocessed_cases = preprocess_data(raw_cases)

        subs = fetch_open_submissions(request.user.bsn)

        # replace raw_cases with preprocessed_cases
        all_cases = raw_cases + subs

        # processed_cases = [case.preprocess_data() for case in all_cases]

        context["cases"] = all_cases[: cls.limit]

        return context

    @classmethod
    def as_htmx_view(cls):
        # this could be generalized to a mixin
        def _view(request):
            if not request.htmx:
                raise BadRequest("requires htmx")
            context = cls.render_htmx_content(request)
            return render(request, cls.render_template, context)

        return _view
