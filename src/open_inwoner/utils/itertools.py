from itertools import islice
from math import ceil


def batched(iterable, chunk_size: int):
    """
    split `iterable `in parts of `chunk_size` length

    implements Python 3.12 itertools.batched()
    """
    iterator = iter(iterable)
    while chunk := tuple(islice(iterator, chunk_size)):
        yield chunk


def split(iterable, num_parts: int = 2):
    """
    split `iterable` in `num_parts` amount of parts
    """
    elements = list(iterable)
    if not elements:
        return []
    chunk_size = ceil(len(elements) / num_parts)
    return batched(elements, chunk_size)
