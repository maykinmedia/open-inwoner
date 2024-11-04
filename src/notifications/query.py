from django.db import models


class NotificationsConfigManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related("notifications_api_service")
