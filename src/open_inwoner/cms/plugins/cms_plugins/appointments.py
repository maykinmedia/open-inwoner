from django.utils.translation import gettext as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from open_inwoner.cms.plugins.models.appointments import UserAppointments
from open_inwoner.qmatic.services import get_appointments_for_user


@plugin_pool.register_plugin
class UserAppointmentsPlugin(CMSPluginBase):
    model = UserAppointments
    module = _("General")
    name = _("My appointments")
    render_template = "cms/plugins/appointments/appointments.html"

    def render(self, context, instance, placeholder):
        request = context["request"]
        appointments = (
            get_appointments_for_user(request.user)
            if request.user.is_authenticated
            else []
        )

        context.update(
            {
                "instance": instance,
                "appointments": appointments,
            }
        )
        return context
