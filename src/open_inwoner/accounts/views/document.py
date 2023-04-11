from django.utils.translation import gettext as _

from privates.views import PrivateMediaView

from open_inwoner.accounts.models import Document
from open_inwoner.utils.views import LogMixin


class DocumentPrivateMediaView(LogMixin, PrivateMediaView):
    model = Document
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    file_field = "file"

    def has_permission(self):
        """
        Override this method to customize the way permissions are checked.
        """
        object = self.get_object()
        if not self.request.user.is_authenticated:
            return False  # If user is not authenticated, the file is not visible

        if (
            self.request.user == object.owner
            or self.request.user.is_superuser
            or (object.plan and self.request.user in object.plan.plan_contacts.all())
        ):
            self.log_user_action(object, _("file was downloaded"))
            return True

        return False
