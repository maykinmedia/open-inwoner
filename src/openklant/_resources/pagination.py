from typing import Generic, TypedDict, TypeVar

T = TypeVar("T")


class PaginatedResponseBody(Generic[T], TypedDict):
    count: int
    next: str | None
    previous: str | None
    results: list[T]
