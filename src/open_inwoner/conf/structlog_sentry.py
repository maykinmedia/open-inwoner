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
from sentry_sdk.utils import event_from_exception
from structlog.types import EventDict, WrappedLogger


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
    ):
        """
        Initialize the Sentry processor.

        Args:
            level: Minimum level for breadcrumbs (default: INFO)
            event_level: Minimum level for Sentry events (default: ERROR)
        """
        self.level = level
        self.event_level = event_level

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
            try:
                full_message = log_record.getMessage()
                if "sentry_event_id" in str(full_message):
                    return None
            except Exception:  # noqa: S110
                # Silently ignore - we're in a Sentry filter hook, logging here
                # could cause infinite loops
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
        # Skip if explicitly requested
        if event_dict.pop("sentry_skip", False):
            return event_dict

        # Check if logger is in ignored list
        logger_name = event_dict.get("logger")
        if logger_name and any(
            logger_name.startswith(ignored) for ignored in _IGNORED_LOGGERS
        ):
            return event_dict

        # Get the log level
        level_name = event_dict.get("level", "").upper()
        try:
            level_value = getattr(logging, level_name, logging.INFO)
        except AttributeError:
            level_value = logging.INFO

        # Only process if level is high enough
        if level_value < self.event_level:
            return event_dict

        # Extract exception info and convert to standard tuple format
        exc_info = event_dict.get("exc_info")
        match exc_info:
            case None:
                return event_dict
            case tuple():
                exc_tuple = exc_info
            case BaseException():
                exc_tuple = (type(exc_info), exc_info, exc_info.__traceback__)
            case True:
                exc_tuple = sys.exc_info()
            case _:
                return event_dict

        # Return early if we don't have a valid exception
        if not exc_tuple or exc_tuple == (None, None, None) or exc_tuple[1] is None:
            return event_dict

        try:
            with sentry_sdk.push_scope() as scope:
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
                        try:
                            # Try to add the value as-is, Sentry will serialize it
                            scope.set_extra(key, value)
                        except Exception:
                            # If that fails, convert to string
                            scope.set_extra(key, str(value))

                # If there's a log message, use it as the event title
                if event_message := event_dict.get("event"):
                    scope.set_tag("log_message", str(event_message))

                    client = sentry_sdk.get_client()
                    event, hint = event_from_exception(
                        exc_tuple,
                        client_options=client.options,
                        mechanism={"type": "logging", "handled": True},
                    )

                    # Set the event message as the main title
                    event["message"] = str(event_message)

                    event_id = sentry_sdk.capture_event(event, hint=hint)
                else:
                    # No custom message, just capture the exception normally
                    event_id = sentry_sdk.capture_exception(exc_tuple[1])

                # Add a marker to the event dict for the before_send hook to detect duplicates
                if event_id:
                    event_dict["sentry_event_id"] = event_id
        except Exception:  # noqa: S110
            # Don't let Sentry processing break the logging pipeline
            # We can't log here as it could cause infinite loops
            pass

        return event_dict
