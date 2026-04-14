from typing import Protocol, Self

from .service.jaaropgave import JaarOpgaveInfoResponse
from .service.uitkering import (
    UitkeringsSpecificatieInfoResponse as UitkeringInfoResponse,
)


class Melding(Protocol):
    code: str | None
    tekst: str | None


class SSDClientException(Exception):
    """Exception class for technical errors (config issues, network errors, malformed XML etc.)"""

    def __init__(self, message: str | None = None):
        super().__init__(message or "SSD client error")


class SSDServiceFaultException(Exception):
    """Exception class for domain faults (valid XML response with 'fout' code)"""

    def __init__(self, meldingen: list[Melding], message: str | None = None):
        self.meldingen = meldingen
        super().__init__(message)

    @classmethod
    def from_xml_response(
        cls, xml_response: JaarOpgaveInfoResponse | UitkeringInfoResponse
    ) -> Self:
        # fout, waarschuwing, informatie (the exception is raised only for fout)
        fwi = xml_response.fwi
        teksten = ", ".join(m.tekst for m in fwi.fout if m.tekst)

        return cls(meldingen=fwi.fout, message=teksten)
