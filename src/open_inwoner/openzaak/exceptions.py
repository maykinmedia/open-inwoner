from typing import Sequence


class InvalidAuth(Exception):
    pass


class NoSubscriptionForClientID(InvalidAuth):
    def __init__(self, client_id):
        self.client_id = client_id
        super().__init__(f"no subscriptions for client_id '{client_id}'")


class InvalidAuthForClientID(InvalidAuth):
    def __init__(self, client_id):
        self.client_id = client_id
        super().__init__(f"secret invalid for subscription client_id'{client_id}'")


class MultiZgwClientProxyError(ExceptionGroup):
    """A container for exceptions raise within individual client requests."""

    def __new__(cls, exceptions: Sequence[Exception]):
        self = super().__new__(
            MultiZgwClientProxyError,
            "One of more ZGW clients raised an error",
            exceptions,
        )
        return self

    def derive(self, exceptions: Sequence[Exception]):
        return MultiZgwClientProxyError(exceptions)
