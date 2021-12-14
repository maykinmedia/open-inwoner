from datetime import datetime
from enum import Enum
from typing import Any, TypedDict


# The next bit is inspired by MessageKit
# https://github.com/MessageKit/MessageKit/blob/master/Documentation/QuickStart.md


class Sender(TypedDict):
    sender_id: str
    display_name: str


class MessageKind(Enum):
    TEXT = 'text'


class Message(TypedDict):
    sender: Sender
    message_id: str
    sent_datetime: datetime
    kind: MessageKind
    data: Any
