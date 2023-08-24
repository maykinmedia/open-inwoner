from itertools import islice
from math import ceil
from typing import Iterable, Iterator, Tuple, TypeVar

T = TypeVar("T")


def batched(iterable: Iterable[T], chunk_size: int) -> Iterator[Tuple[T, ...]]:
    """
    split `iterable `in parts of `chunk_size` length

    implements Python 3.12 itertools.batched()
    """
    iterator = iter(iterable)
    while chunk := tuple(islice(iterator, chunk_size)):
        yield chunk


def split(iterable: Iterable[T], num_parts: int = 2) -> Iterator[Tuple[T, ...]]:
    """
    split `iterable` in `num_parts` amount of parts
    """
    elements = list(iterable)
    if not elements:
        return []
    chunk_size = ceil(len(elements) / num_parts)
    return batched(elements, chunk_size)
