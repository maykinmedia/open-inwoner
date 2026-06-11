from typing import NotRequired

from typing_extensions import TypedDict


class PartijUpdateData(TypedDict):
    email: NotRequired[str]
    phonenumber: NotRequired[str]
