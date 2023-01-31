import logging

from django.utils.encoding import force_str

from timeline_logger.models import TimelineLog


class Lookups:
    """
    lookups for the message of a JSONField
    """

    exact = "exact"
    icontains = "icontains"

    startswith = "startswith"
    istartswith = "istartswith"
    endswith = "endswith"
    iendswith = "iendswith"
    iexact = "iexact"
    regex = "regex"
    iregex = "iregex"


class AssertTimelineLogMixin:
    def assertTimelineLog(
        self, message, *, level=None, lookup=Lookups.exact
    ) -> TimelineLog:
        kwargs = {
            f"extra_data__message__{lookup}": force_str(message),
        }
        if level is not None:
            kwargs["extra_data__log_level"] = level

        logs = list(TimelineLog.objects.filter(**kwargs))
        count = len(logs)
        if count == 0:
            self.fail(
                f"cannot find TimelineLog with {kwargs}, got:\n{self.getTimelineLogDump()}"
            )
        elif count > 1:
            self.fail(
                f"found {count} TimelineLogs with {kwargs}, got:\n{self.getTimelineLogDump()}"
            )

        return logs[0]

    def getTimelineLogDump(self) -> str:
        ret = []
        qs = TimelineLog.objects.all()
        c = qs.count()
        ret.append(f"total {c} timelinelogs")
        for log in qs:
            message = log.extra_data.get("message")
            log_level = log.extra_data.get("log_level")
            if log_level:
                log_level = logging.getLevelName(log_level)
            else:
                log_level = "NO_LEVEL"
            msg = f"{log_level}: {message}"
            ret.append(msg)
        return "\n".join(ret)

    def dumpTimelineLog(self):
        print(self.getTimelineLogDump())
