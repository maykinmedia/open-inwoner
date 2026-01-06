from django.utils.translation import gettext as _

import structlog
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from open_inwoner.qmatic.client import NoServiceConfigured, qmatic_client_factory

from .models import UserAppointments

logger = structlog.stdlib.get_logger(__name__)


@plugin_pool.register_plugin
class UserAppointmentsPlugin(CMSPluginBase):
    model = UserAppointments
    module = _("Profile")
    name = _("My appointments")
    render_template = "mijn_profiel/appointments.html"

    def render(self, context, instance, placeholder):
        request = context["request"]
        if not request.user.is_authenticated or not request.user.has_verified_email():
            appointments = []
        else:
            try:
                client = qmatic_client_factory()
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
