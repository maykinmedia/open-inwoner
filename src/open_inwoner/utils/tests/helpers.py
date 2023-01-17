import logging

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
    def assertTimelineLog(self, message, *, level=None, lookup=Lookups.exact):
        kwargs = {
            f"extra_data__message__{lookup}": message,
        }
        if level is not None:
            kwargs["extra_data__log_level"] = level

        logs = list(TimelineLog.objects.filter(**kwargs))
        count = len(logs)
        if count == 0:
            self.dumpTimelineLog()
            self.fail(f"cannot find TimelineLog with {kwargs}")
        elif count > 1:
            self.dumpTimelineLog()
            self.fail(f"found {count} TimelineLogs with {kwargs}")

        return logs[0]

    def dumpTimelineLog(self):
        qs = TimelineLog.objects.all()
        c = qs.count()
        print(f"total {c} timelinelogs")
        for log in qs:
            message = log.extra_data.get("message")
            log_level = log.extra_data.get("log_level")
            if log_level:
                log_level = logging.getLevelName(log_level)
            else:
                log_level = "NO_LEVEL"
            msg = f"{log_level}: {message}"
            print(msg)
