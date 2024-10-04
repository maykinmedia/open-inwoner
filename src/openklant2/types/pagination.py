from typing import Generic, Required, TypeVar

from typing_extensions import TypedDict

T = TypeVar("T")


class PaginatedResponseBody(Generic[T], TypedDict):
    count: Required[int]
    next: Required[str | None]
    previous: Required[str | None]
    results: Required[list[T]]
