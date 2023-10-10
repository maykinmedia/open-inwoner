from dataclasses import dataclass, field
from typing import Optional

from open_inwoner.ssd.service.uitkering.body_action_resolved import (
    UitkeringsSpecificatieInfo,
)
from open_inwoner.ssd.service.uitkering.body_reaction_resolved import (
    UitkeringsSpecificatieInfoResponse,
)
from open_inwoner.ssd.service.uitkering.fwi_resolved import Fwi
from open_inwoner.ssd.service.uitkering.gwsmlheader_resolved import Header

__NAMESPACE__ = "http://www.centric.nl/GWS/Diensten/UitkeringsSpecificatieClient/v0600"


@dataclass
class UitkeringsSpecificatieClientPortTypeSendUitkeringsSpecificatieClientInput:
    class Meta:
        name = "Envelope"
        namespace = "http://schemas.xmlsoap.org/soap/envelope/"

    header: Optional[
        "UitkeringsSpecificatieClientPortTypeSendUitkeringsSpecificatieClientInput.Header"
    ] = field(
        default=None,
        metadata={
            "name": "Header",
            "type": "Element",
        },
    )
    body: Optional[
        "UitkeringsSpecificatieClientPortTypeSendUitkeringsSpecificatieClientInput.Body"
    ] = field(
        default=None,
        metadata={
            "name": "Body",
            "type": "Element",
        },
    )

    @dataclass
    class Header:
        header: Optional[Header] = field(
            default=None,
            metadata={
                "name": "Header",
                "type": "Element",
                "namespace": "http://www.centric.nl/GWS/Header/v0300",
            },
        )

    @dataclass
    class Body:
        uitkerings_specificatie_info: Optional[UitkeringsSpecificatieInfo] = field(
            default=None,
            metadata={
                "name": "UitkeringsSpecificatieInfo",
                "type": "Element",
                "namespace": "http://www.centric.nl/GWS/Diensten/UitkeringsSpecificatieClient/v0600",
            },
        )


@dataclass
class UitkeringsSpecificatieClientPortTypeSendUitkeringsSpecificatieClientOutput:
    class Meta:
        name = "Envelope"
        namespace = "http://schemas.xmlsoap.org/soap/envelope/"

    header: Optional[
        "UitkeringsSpecificatieClientPortTypeSendUitkeringsSpecificatieClientOutput.Header"
    ] = field(
        default=None,
        metadata={
            "name": "Header",
            "type": "Element",
        },
    )
    body: Optional[
        "UitkeringsSpecificatieClientPortTypeSendUitkeringsSpecificatieClientOutput.Body"
    ] = field(
        default=None,
        metadata={
            "name": "Body",
            "type": "Element",
        },
    )

    @dataclass
    class Header:
        header: Optional[Header] = field(
            default=None,
            metadata={
                "name": "Header",
                "type": "Element",
                "namespace": "http://www.centric.nl/GWS/Header/v0300",
            },
        )

    @dataclass
    class Body:
        uitkerings_specificatie_info_response: Optional[
            UitkeringsSpecificatieInfoResponse
        ] = field(
            default=None,
            metadata={
                "name": "UitkeringsSpecificatieInfoResponse",
                "type": "Element",
                "namespace": "http://www.centric.nl/GWS/Diensten/UitkeringsSpecificatieClient/v0600",
            },
        )
        fault: Optional[
            "UitkeringsSpecificatieClientPortTypeSendUitkeringsSpecificatieClientOutput.Body.Fault"
        ] = field(
            default=None,
            metadata={
                "name": "Fault",
                "type": "Element",
            },
        )

        @dataclass
        class Fault:
            faultcode: Optional[str] = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "",
                },
            )
            faultstring: Optional[str] = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "",
                },
            )
            faultactor: Optional[str] = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "",
                },
            )
            detail: Optional[
                "UitkeringsSpecificatieClientPortTypeSendUitkeringsSpecificatieClientOutput.Body.Fault.Detail"
            ] = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "",
                },
            )

            @dataclass
            class Detail:
                fwi: Optional[Fwi] = field(
                    default=None,
                    metadata={
                        "name": "FWI",
                        "type": "Element",
                        "namespace": "http://www.centric.nl/GWS/FWI/v0200",
                    },
                )


class UitkeringsSpecificatieClientPortTypeSendUitkeringsSpecificatieClient:
    uri = "#UitkeringsSpecificatieClientPolicy"
    name = "SendUitkeringsSpecificatie"
    style = "document"
    location = "No target address"
    transport = "http://schemas.xmlsoap.org/soap/http"
    input = UitkeringsSpecificatieClientPortTypeSendUitkeringsSpecificatieClientInput
    output = UitkeringsSpecificatieClientPortTypeSendUitkeringsSpecificatieClientOutput
