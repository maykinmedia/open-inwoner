from typing_extensions import TypedDict


class ListContentLabelParams(TypedDict, total=False):
    """Query parameters for listing content labels."""

    page: int


class ContentLabel(TypedDict):
    """ContentLabel response object."""

    naam: str
