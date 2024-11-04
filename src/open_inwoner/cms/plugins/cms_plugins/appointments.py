import logging

from django.utils.translation import gettext as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from open_inwoner.cms.plugins.models.appointments import UserAppointments
from open_inwoner.qmatic.client import NoServiceConfigured, QmaticClient

logger = logging.getLogger(__name__)


@plugin_pool.register_plugin
class UserAppointmentsPlugin(CMSPluginBase):
    model = UserAppointments
    module = _("General")
    name = _("My appointments")
    render_template = "cms/plugins/appointments/appointments.html"

    def render(self, context, instance, placeholder):
        request = context["request"]
        if not request.user.is_authenticated or not request.user.has_verified_email():
            appointments = []
        else:
            try:
                client = QmaticClient()
            except NoServiceConfigured:
                logger.exception("Error occurred while creating Qmatic client")
                appointments = []
            else:
                appointments = client.list_appointments_for_customer(
                    request.user.verified_email
                )

        context.update(
            {
                "instance": instance,
                "appointments": appointments,
            }
        )
        return context
