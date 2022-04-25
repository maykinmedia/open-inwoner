from django.conf import settings

from open_inwoner.accounts.models import User


class SplitSessionAge:
    def get_session_cookie_age(self):
        user_id = self.get("_auth_user_id")

        try:
            is_staff = User.objects.get(pk=user_id).is_staff
        except Exception:
            is_staff = False

        if hasattr(settings, "SESSION_COOKIE_AGE_ADMIN") and is_staff:
            return settings.SESSION_COOKIE_AGE_ADMIN
        return settings.SESSION_COOKIE_AGE
