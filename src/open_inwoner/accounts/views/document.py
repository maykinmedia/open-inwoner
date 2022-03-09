from privates.views import PrivateMediaView

from open_inwoner.accounts.models import Document


class DocumentPrivateMediaView(PrivateMediaView):
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

        if self.request.user == object.owner or self.request.user.is_superuser:
            return True

        return False
