import typing

from open_inwoner.accounts.models import User


class Notifier(typing.Protocol):
    def __call__(self, receiver: User, object_ids: list[int], channel: str) -> None:
        ...
