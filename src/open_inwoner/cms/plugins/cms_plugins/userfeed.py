from django.utils.translation import gettext as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from open_inwoner.cms.plugins.models.userfeed import UserFeed
from open_inwoner.userfeed.feed import get_feed


@plugin_pool.register_plugin
class UserFeedPlugin(CMSPluginBase):
    model = UserFeed
    module = _("General")
    name = _("User Feed")
    render_template = "cms/plugins/userfeed/userfeed.html"

    def render(self, context, instance, placeholder):
        request = context["request"]
        feed = get_feed(request.user)

        feed_items_list = [
            {
                "title": item.title,
                "message": item.message,
                "action_text": item.action_text,
                "action_url": item.action_url,
            }
            for item in feed.items
        ]

        context.update(
            {
                "instance": instance,
                "userfeed": feed,
                "userfeed_item_list_json": feed_items_list,
            }
        )
        return context
