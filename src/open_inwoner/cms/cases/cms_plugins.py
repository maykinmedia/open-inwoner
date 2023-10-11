from django.utils.translation import ugettext_lazy as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

# TODO: import `preprocess_data` after merge of PR 804
from open_inwoner.openzaak.cases import fetch_cases
from open_inwoner.openzaak.formapi import fetch_open_submissions

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

        raw_cases = [
            case for case in fetch_cases(request.user.bsn) if not case.einddatum
        ]
        # TODO
        # preprocessed_cases = preprocess_data(raw_cases)

        subs = fetch_open_submissions(request.user.bsn)

        # replce raw_cases with preprocessed_cases
        all_cases = raw_cases + subs

        # processed_cases = [case.preprocess_data() for case in all_cases]

        context["cases"] = all_cases[: self.limit]

        return context
