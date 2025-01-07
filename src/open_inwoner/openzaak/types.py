from typing import Protocol


class UniformCase(Protocol):
    """
    Zaken and open submissions are classified as "cases" if they have an
    `identification` property and a method `process_data` to prepare data
    for the template
    """

    @property
    def identification(self) -> str:
        ...

    def process_data(self) -> dict:
        """
        Prepare data for template

        Should include (at least) the following:
            - identification (str)
            - uuid (str)
            - case_type (str)
        """
        ...
