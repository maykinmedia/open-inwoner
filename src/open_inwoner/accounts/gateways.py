import functools
import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

import messagebird

from open_inwoner.utils.text import mask_phone_number, mask_sensitive_data

logger = logging.getLogger(__name__)


_mask_token_message = functools.partial(
    mask_sensitive_data, visible_start=2, visible_end=2, min_length=8
)


class GatewayError(Exception):
    """
    Something went wrong while sending the
    text message.
    """


class Gateway:
    def get_message(self, token):
        msg = getattr(settings, "ACCOUNTS_SMS_MESSAGE", "Your token is: {token}")
        return msg.format(token=token)

    def send(self, to, token, **kwargs):
        raise NotImplementedError()


class Dummy(Gateway):
    def send(self, to, token, **kwargs):
        logger.info(
            '(Dummy) Sent SMS to {to} by "{orig}": "{msg}"'.format(
                to=mask_phone_number(to),
                orig="oip",
                msg=_mask_token_message(self.get_message(token)),
            )
        )
        return True


class FailureDummy(Gateway):
    """
    Dummy gateway which can be used to test the failure case.
    """

    def send(self, to, token, **kwargs):
        raise GatewayError()


class MessageBird(Gateway):
    def __init__(self):
        """
        Validate settings on initialization.
        """
        self.settings = getattr(settings, "ACCOUNTS_SMS_GATEWAY", {})
        if not all([k in self.settings for k in ["API_KEY", "ORIGINATOR"]]):
            raise ImproperlyConfigured(
                "Missing SMS gateway settings in ACCOUNTS_SMS_GATEWAY."
            )

    def send(self, to, token, **kwargs):
        client = messagebird.Client(settings.ACCOUNTS_SMS_GATEWAY.get("API_KEY"))

        try:
            response = client.message_create(
                settings.ACCOUNTS_SMS_GATEWAY.get("ORIGINATOR"),
                to,
                self.get_message(token),
            )
        except messagebird.client.ErrorException as exc:
            for error in exc.errors:
                logger.critical(("Could not send SMS:\n{error}").format(error=error))
            raise GatewayError() from exc
        else:
            logger.debug(
                "Successfully sent SMS",
                extra={
                    "to": mask_phone_number(to),
                    "message": _mask_token_message(self.get_message(token)),
                },
            )
            return True


gateway = import_string(
    getattr(
        settings,
        "ACCOUNTS_SMS_GATEWAY",
        {"BACKEND": "accounts.gateways.Dummy"},
    )["BACKEND"]
)()
