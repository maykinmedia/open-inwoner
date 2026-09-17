from django.utils.translation import gettext_lazy as _

from django_yubin.models import Log as YubinLog, Message as YubinMessage


class EmailLog(YubinLog):
    """
    Proxy for django_yubin's ``Log`` model.

    django_yubin's own ``verbose_name`` is just "log", which reads as
    confusingly generic in the admin index (it sits right next to
    ``timeline_logger``'s "timeline log entries"). Since we can't change
    django_yubin's ``Meta`` directly, a proxy model lets us give it a
    clearer name without touching the underlying table.
    """

    class Meta:
        proxy = True
        verbose_name = _("e-mail verzendlog")
        verbose_name_plural = _("e-mail verzendlogs")


class EmailMessage(YubinMessage):
    """
    Proxy for django_yubin's ``Message`` model.

    django_yubin's own ``verbose_name`` is just "message", which is
    indistinguishable from ``accounts.Message`` (a citizen-to-citizen chat
    message) in the admin index. A proxy gives it a clearer, unambiguous
    name without touching django_yubin's underlying table.
    """

    class Meta:
        proxy = True
        verbose_name = _("verzonden e-mail")
        verbose_name_plural = _("verzonden e-mails")
