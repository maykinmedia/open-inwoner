from django.utils.translation import gettext as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from ..models import TasksConfig


@plugin_pool.register_plugin
class TasksPlugin(CMSPluginBase):
    """
    Uses the Objects API to retrieve and show tasks according to the MijnTaken Objecttypes schema
    Reuses the UserFeedPlugin template
    """

    model = TasksConfig
    name = _("Task list Plugin")
    render_template = "cms/plugins/tasks/tasks.html"
    cache = False

    def render(self, context, instance, placeholder):
        request = context["request"]
        context["instance"] = instance
        context["tasks"] = []

        if request.user.is_authenticated and (bsn := request.user.bsn):
            tasks = instance.get_tasks_by_bsn(bsn)
            for task in tasks:
                task["task_url"] = task["url"]["uri"]
            context["tasks"] = tasks
        return context
