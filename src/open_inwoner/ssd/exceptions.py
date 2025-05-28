from typing import Self

from .service.jaaropgave import JaarOpgaveInfoResponse
from .service.uitkering import (
    UitkeringsSpecificatieInfoResponse as UitkeringInfoResponse,
)


class SSDClientException(Exception):
    response: JaarOpgaveInfoResponse | UitkeringInfoResponse | None

    def __init__(self, message: str | None = None):
        super().__init__(message or "SSD client error")

    @classmethod
    def from_xml_response(
        cls, xml_response: JaarOpgaveInfoResponse | UitkeringInfoResponse
    ) -> Self:
        # fout, waarschuwing, informatie
        fwi = xml_response.fwi
        error_messages = ", ".join(
            e.tekst for e in (fwi.fout or fwi.waarshuwing or fwi.informatie,) if e
        )

        return cls(message=error_messages)
