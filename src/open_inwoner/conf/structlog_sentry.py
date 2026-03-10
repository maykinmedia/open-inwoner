"""
Custom structlog processor for Sentry integration.

This processor captures exceptions from structlog events and sends them to Sentry
BEFORE format_exc_info runs, ensuring Sentry receives raw exception objects with
full stack traces instead of formatted strings or JSON blobs.
"""

import logging  # noqa: TID251 - Used for log level constants only
import sys

import sentry_sdk
from sentry_sdk.integrations.logging import _IGNORED_LOGGERS
from structlog.types import EventDict, WrappedLogger

IGNORED_LOGGERS: set[str] = _IGNORED_LOGGERS | {
    "log_outgoing_requests",
    "save_outgoing_requests",
    "django_structlog.middlewares.request",
}


class SentryStructlogProcessor:
    """
    Structlog processor that sends exceptions to Sentry when both conditions are met.

    Events are sent to Sentry ONLY when ALL of the following conditions are true:
    1. The log level is at or above the configured threshold (default: ERROR)
    2. The event contains exception info (exc_info is present and valid)
    3. The processor is active (can be disabled via the active flag)
    4. The logger is not in the ignored list

    This ensures that only genuine exceptions at appropriate severity levels are
    captured, preventing noise from regular log messages or low-severity events.

    The processor intercepts log events containing exceptions and captures them with
    full context before they're formatted into strings. This ensures Sentry receives
    rich exception objects with proper stack traces, type information, and metadata
    rather than formatted text representations.

    This processor should be placed BEFORE format_exc_info in the processor chain
    to ensure it captures raw exception objects.
    """

    level: int
    active: bool

    def __init__(
        self,
        level: int = logging.ERROR,
        active: bool = True,
    ):
        """
        Initialize the Sentry processor.

        Args:
            level: Minimum level for capturing exceptions (default: logging.ERROR)
            active: Whether the processor is active (default: True)
        """
        self.level = level
        self.active = active

    def _can_record(self, logger_name: str | None) -> bool:
        if not logger_name:
            return True

        return not any(logger_name.startswith(ignored) for ignored in IGNORED_LOGGERS)

    def _get_log_level(self, event_dict: EventDict) -> int:
        level_name = event_dict.get("level", "").upper()
        return getattr(logging, level_name, logging.INFO)

    def _make_safe_for_sentry(self, value, depth=0, max_depth=10):
        """
        Convert a value to a safe type for Sentry that won't trigger database queries.

        Non-primitive types (Django models, querysets, lazy objects) are replaced with
        placeholders to avoid two critical issues:
        1. Database access: Accessing model attributes/relationships during exception
           handling can trigger queries, potentially interfering with ongoing transactions
           or causing deadlocks in error scenarios.
        2. Serialization failures: Complex objects may not serialize to JSON properly,
           causing Sentry reporting itself to fail and losing the exception entirely.

        Being defensive here ensures that exception reporting is robust and never causes
        additional errors or side effects during the critical error handling path.

        Args:
            value: The value to convert
            depth: Current recursion depth (for internal use)
            max_depth: Maximum recursion depth to prevent stack overflow

        Returns:
            The value if it's a safe primitive, otherwise a placeholder string
        """
        # Prevent infinite recursion from deeply nested or circular structures
        if depth >= max_depth:
            return "<max_depth_exceeded>"

        match value:
            # Handle primitives that are already safe
            case None | bool() | int() | float() | str():
                return value
            # Handle collections recursively
            case dict():
                return {
                    k: self._make_safe_for_sentry(v, depth + 1, max_depth)
                    for k, v in value.items()
                }
            case list() | tuple() | set():
                return [
                    self._make_safe_for_sentry(item, depth + 1, max_depth)
                    for item in value
                ]
            # For anything else (Django models, querysets, lazy objects, etc.),
            # use a placeholder to avoid database access or serialization issues
            case _:
                return f"<{type(value).__name__}>"

    def _extract_exc_info(self, event_dict: EventDict) -> tuple | None:
        """
        Extract exception info and normalize to tuple format.

        Args:
            event_dict: The structlog event dictionary

        Returns:
            Exception info as a tuple (type, value, traceback) or None if no valid exception
        """
        exc_info = event_dict.get("exc_info")
        match exc_info:
            case None:
                return None
            case tuple():
                exc_tuple = exc_info
            case BaseException():
                exc_tuple = (type(exc_info), exc_info, exc_info.__traceback__)
            case True:
                exc_tuple = sys.exc_info()
            case _:
                return None

        # Validate we have a real exception
        if not exc_tuple or exc_tuple == (None, None, None) or exc_tuple[1] is None:
            return None

        return exc_tuple

    def _add_context_to_scope(self, scope, event_dict: EventDict) -> None:
        """
        Add structlog event context to Sentry scope.

        Args:
            scope: The Sentry scope to add context to
            event_dict: The structlog event dictionary
        """
        # Add all event_dict fields as extra context
        # Eagerly serialize values to prevent database access during Sentry processing
        for key, value in event_dict.items():
            if key in (
                "exc_info",
                "timestamp",
            ):
                continue

            # Eagerly convert to safe types to avoid database queries during
            # Sentry processing. This prevents interference with ongoing transactions.
            safe_value = self._make_safe_for_sentry(value)
            scope.set_extra(key, safe_value)

        # Add log message as a tag for searchability and visibility Note: The 'event'
        # field is also added to extras above, but we add it as a tag too because:
        # 1. Tags are indexed and searchable in Sentry UI (can filter by
        #    log_message:"error text")
        # 2. Tags show prominently in the Sentry UI tags section
        # 3. Extras are for detailed context, tags are for filtering/grouping
        if event_message := event_dict.get("event"):
            # Only add string messages as tags to avoid serialization issues
            if isinstance(event_message, str):
                scope.set_tag("log_message", event_message)

    def _capture_to_sentry(self, event_dict: EventDict, exc_tuple: tuple) -> str | None:
        """
        Capture exception to Sentry with event context.

        Args:
            event_dict: The structlog event dictionary
            exc_tuple: The exception info tuple (type, value, traceback)

        Returns:
            The Sentry event ID if successful, None otherwise
        """
        with sentry_sdk.push_scope() as scope:
            self._add_context_to_scope(scope, event_dict)
            # Capture the exception - Sentry will use the exception message as the title
            event_id = sentry_sdk.capture_exception(exc_tuple[1])
            return event_id

    @staticmethod
    def before_send(event, hint):
        """
        Filter out log message events that are duplicates of exceptions already
        captured.

        Our custom SentryStructlogProcessor captures exceptions directly from structlog
        before they're formatted. However, Django's integration also tries to capture
        the formatted log output, resulting in duplicate events where one is a proper
        exception and the other is a JSON blob message.

        This hook filters out the JSON blob messages by checking if:
        1. The event has no exception (it's just a message)
        2. The message looks like it came from structlog (contains 'sentry_event_id')
        3. There's an exception in the hint (meaning an exception was already captured)
        """
        # Check if logger is in ignored list (for events captured by Django's integration)
        if log_record := hint.get("log_record"):
            logger_name = getattr(log_record, "name", None)
            if logger_name and any(
                logger_name.startswith(ignored) for ignored in IGNORED_LOGGERS
            ):
                return None

        # Check if this is a duplicate message event
        # Our SentryProcessor adds 'sentry_event_id' to the log, so if the message
        # contains that, it's a duplicate of an already-sent exception
        message = event.get("message", "")
        if "sentry_event_id" in str(message):
            # This is a duplicate - the real exception was already sent
            return None

        # If this event has an exception, let it through (it's from our SentryStructlogProcessor)
        if event.get("exception"):
            return event

        # Also check the log record's message directly
        if log_record := hint.get("log_record"):
            # Check if the log record has an exception (was already captured)
            if getattr(log_record, "exc_info", None):
                # This is a log message with an exception that was already captured
                # by our SentryStructlogProcessor, so drop it
                return None

            # Check the formatted message from the log record
            record_message = getattr(log_record, "message", "")
            if "sentry_event_id" in str(record_message):
                return None

            # Also check getMessage() which includes formatted args
            # Note: getMessage() should never fail in normal cases, but could raise
            # TypeError if the format string and args don't match. We only catch that.
            try:
                full_message = log_record.getMessage()
                if "sentry_event_id" in str(full_message):
                    return None
            except (TypeError, ValueError):
                # getMessage() can fail if format args don't match the message
                # In that case, just skip this check
                pass

        return event

    def __call__(
        self, logger: WrappedLogger, method_name: str, event_dict: EventDict
    ) -> EventDict:
        """
        Process the event and send to Sentry if appropriate.

        Args:
            logger: The wrapped logger instance
            method_name: The name of the method called (e.g., "info", "error")
            event_dict: The event dictionary

        Returns:
            The unmodified event_dict (this processor doesn't modify events)
        """
        # Early exit if processor is disabled
        if not self.active:
            return event_dict

        # Check if logger should be ignored
        logger_name = event_dict.get("logger")
        if not self._can_record(logger_name):
            return event_dict

        # Check log level threshold
        level_value = self._get_log_level(event_dict)
        if level_value < self.level:
            return event_dict

        # Extract and validate exception info
        exc_tuple = self._extract_exc_info(event_dict)
        if not exc_tuple:
            return event_dict

        # Capture to Sentry and add event ID marker
        if event_id := self._capture_to_sentry(event_dict, exc_tuple):
            event_dict["sentry_event_id"] = event_id

        return event_dict
