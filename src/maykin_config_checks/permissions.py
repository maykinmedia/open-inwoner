from django.utils.translation import gettext as _
class IsSuperUser:
    def has_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def get_error_message(self, obj=None):
        return _("Only superusers may run configuration checks.")
