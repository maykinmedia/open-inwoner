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
    "open_inwoner.utils.logentry",
}


class SentryStructlogProcessor:
    """
    Structlog processor that sends exceptions to Sentry.

    This processor should be placed BEFORE format_exc_info in the processor chain
    to ensure it captures raw exception objects.
    """

    def __init__(
        self,
        level: int = logging.INFO,
        event_level: int = logging.ERROR,
        active: bool = True,
    ):
        """
        Initialize the Sentry processor.

        Args:
            level: Minimum level for breadcrumbs (default: INFO)
            event_level: Minimum level for Sentry events (default: ERROR)
            active: Whether the processor is active (default: True)
        """
        self.level = level
        self.event_level = event_level
        self.active = active

    def _can_record(self, logger_name: str | None) -> bool:
        """
        Check if this logger should be recorded to Sentry.

        Args:
            logger_name: The name of the logger

        Returns:
            True if the logger should be recorded, False otherwise
        """
        if not logger_name:
            return True
        return not any(logger_name.startswith(ignored) for ignored in IGNORED_LOGGERS)

    def _get_log_level(self, event_dict: EventDict) -> int:
        """
        Extract and convert log level from event dict.

        Args:
            event_dict: The structlog event dictionary

        Returns:
            The numeric log level (defaults to INFO if not found)
        """
        level_name = event_dict.get("level", "").upper()
        try:
            return getattr(logging, level_name, logging.INFO)
        except AttributeError:
            return logging.INFO

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
        # Make sure we serialize complex objects to strings
        for key, value in event_dict.items():
            if key not in (
                "exc_info",
                "event",
                "logger",
                "level",
                "timestamp",
            ):
                # Sentry's set_extra should handle serialization
                # IMPORTANT: We let database errors propagate from str()/repr()
                # so they break the transaction properly if they occur
                try:
                    scope.set_extra(key, value)
                except (TypeError, ValueError, AttributeError):
                    # Serialization failed, try as string (may raise DB errors)
                    try:
                        scope.set_extra(key, str(value))
                    except (TypeError, ValueError, AttributeError):
                        # str() failed (not DB errors), try repr
                        scope.set_extra(key, repr(value))

        # Add log message as context if present
        # Note: str() calls may trigger __str__ with DB queries - we let those propagate
        if event_message := event_dict.get("event"):
            scope.set_tag("log_message", str(event_message))

    def _capture_to_sentry(self, event_dict: EventDict, exc_tuple: tuple) -> str | None:
        """
        Capture exception to Sentry with event context.

        Args:
            event_dict: The structlog event dictionary
            exc_tuple: The exception info tuple (type, value, traceback)

        Returns:
            The Sentry event ID if successful, None otherwise
        """
        # Only catch Sentry SDK errors, not database/transaction errors
        # Common Sentry errors: connection issues, rate limiting, client not configured
        try:
            with sentry_sdk.push_scope() as scope:
                self._add_context_to_scope(scope, event_dict)
                # Capture the exception - Sentry will use the exception message as the title
                event_id = sentry_sdk.capture_exception(exc_tuple[1])
                return event_id
        except (
            # Only catch Sentry SDK-specific errors, not database/transaction errors
            TypeError,  # Invalid Sentry SDK arguments
            ValueError,  # Invalid Sentry SDK configuration
            KeyError,  # Missing Sentry event fields
            AttributeError,  # Sentry client not initialized
            RuntimeError,  # Sentry SDK internal errors
            OSError,  # Network errors to Sentry
        ):
            # Silently fail - Sentry errors shouldn't break logging
            # IMPORTANT: We do NOT catch Exception, so database errors will propagate
            # and break the transaction properly if they occur
            return None

    @staticmethod
    def before_send(event, hint):
        """
        Filter out log message events that are duplicates of exceptions already captured.

        Our custom SentryStructlogProcessor captures exceptions directly from structlog before
        they're formatted. However, Django's integration also tries to capture the
        formatted log output, resulting in duplicate events where one is a proper
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

        # If this event has an exception, let it through (it's from our SentryStructlogProcessor)
        if event.get("exception"):
            return event

        # Check if this is a duplicate message event
        # Our SentryProcessor adds 'sentry_event_id' to the log, so if the message
        # contains that, it's a duplicate of an already-sent exception
        message = event.get("message", "")
        if "sentry_event_id" in str(message):
            # This is a duplicate - the real exception was already sent
            return None

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
        if level_value < self.event_level:
            return event_dict

        # Extract and validate exception info
        exc_tuple = self._extract_exc_info(event_dict)
        if not exc_tuple:
            return event_dict

        # Capture to Sentry and add event ID marker
        if event_id := self._capture_to_sentry(event_dict, exc_tuple):
            event_dict["sentry_event_id"] = event_id

        return event_dict
