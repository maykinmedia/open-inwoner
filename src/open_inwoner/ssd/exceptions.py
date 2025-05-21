from typing import Self

from .service.jaaropgave import JaarOpgaveInfoResponse
from .service.uitkering import (
    UitkeringsSpecificatieInfoResponse as UitkeringInfoResponse,
)


class SSDClientException(Exception):
    def __init__(self, message=None):
        super().__init__(message)
        self.message = message

    @classmethod
    def from_xml_response(
        cls, xml_response: JaarOpgaveInfoResponse | UitkeringInfoResponse
    ) -> Self:
        # fout, waarshuwing, informatie
        fwi = xml_response.fwi

        exceptions = fwi.fout or fwi.waarshuwing or fwi.informatie
        if not exceptions:
            return cls("SSD client error")

        melding = exceptions[0]

        return cls(message=melding.tekst)
