# from cms.plugin_base import CMSPluginBase
# from cms.plugin_pool import plugin_pool
# from django.utils.translation import gettext as _


# @plugin_pool.register_plugin  # register the plugin
# class PollPluginPublisher(CMSPluginBase):
#     module = _("SSD")
#     name = _("SSD Plugin")  # name of the plugin in the interface
#     app_hook = "SSDApphook"
#     render_template = "open_inwoner/ssd/benefits_overview.html"
#     cache = False

#     def render(self, context, instance, placeholder):
#         # context.update({'instance': instance})
#         context.update({'test': test})
#         return context
