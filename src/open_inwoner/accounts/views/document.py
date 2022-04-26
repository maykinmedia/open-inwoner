from django.utils.translation import ugettext_lazy as _

from privates.views import PrivateMediaView

from open_inwoner.accounts.models import Document
from open_inwoner.utils.logentry import LogMixin


class DocumentPrivateMediaView(LogMixin, PrivateMediaView):
    model = Document
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    file_field = "file"

    def has_permission(self):
        """
        Override this method to customize the way permissions are checked.
        """
        print("has_permission")
        object = self.get_object()
        if not self.request.user.is_authenticated:
            return False  # If user is not authenticated, the file is not visible

        if self.request.user == object.owner or self.request.user.is_superuser:
            self.log_user_action(object, str(_("file was downloaded")))
            return True

        return False
