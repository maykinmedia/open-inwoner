from typing import NotRequired

from typing_extensions import TypedDict


class ListContentElementParams(TypedDict, total=False):
    """Query parameters for listing content elements."""

    labels: list[str]
    exclude_labels: list[str]
    page: int


class ContentElement(TypedDict):
    """ContentElement response object."""

    uuid: str
    content: str
    aanvullende_informatie: NotRequired[str]
    labels: NotRequired[list[str]]
    producttype_uuid: str
    taal: str


class NestedContentElement(TypedDict):
    """Nested ContentElement object."""

    uuid: str
    taal: str
    content: str
    aanvullende_informatie: NotRequired[str]
    labels: NotRequired[list[str]]
