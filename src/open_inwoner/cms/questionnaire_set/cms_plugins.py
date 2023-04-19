from django.utils.translation import ugettext_lazy as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from open_inwoner.questionnaire.models import QuestionnaireStep


@plugin_pool.register_plugin
class QuestionnairePlugin(CMSPluginBase):
    module = _("Questionnaire")
    name = _("Questionnaire Plugin")
    render_template = "cms/questionnaire/questionnaire_plugin.html"

    def render(self, context, instance, placeholder):
        context["questionnaire_roots"] = QuestionnaireStep.get_root_nodes().filter(
            highlighted=True, published=True
        )
        return context
