from typing import Protocol


class UniformCase(Protocol):
    """
    Zaaken and open submissions are classified as "cases" if they have an
    `identificatie` attribute and a method `process_data` to prepare data
    for the template
    """

    identificatie: str

    def process_data(self) -> dict:
        ...
