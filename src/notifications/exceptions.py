class NotificationError(Exception):
    """Base class for all notification exceptions."""

    pass


class NotificationRecordLockError(NotificationError):
    """Raised when a notification record cannot be locked for processing (concurrent access)."""

    pass


class NotificationAlreadyProcessedError(NotificationError):
    """Raised when a notification record has already reached a final state."""

    pass


class NotificationSkippedException(NotificationError):
    """Raised when a notification should be marked as skipped rather than failed."""

    pass
