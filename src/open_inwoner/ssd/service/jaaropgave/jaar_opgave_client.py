from dataclasses import dataclass, field

from open_inwoner.ssd.service.jaaropgave.body_action_resolved import JaarOpgaveInfo
from open_inwoner.ssd.service.jaaropgave.body_reaction_resolved import (
    JaarOpgaveInfoResponse,
)
from open_inwoner.ssd.service.jaaropgave.fwi_resolved import Fwi
from open_inwoner.ssd.service.jaaropgave.gwsmlheader_resolved import Header

__NAMESPACE__ = "http://www.centric.nl/GWS/Diensten/JaarOpgaveClient/v0400"


@dataclass
class JaarOpgaveClientPortTypeSendJaarOpgaveClientInput:
    class Meta:
        name = "Envelope"
        namespace = "http://schemas.xmlsoap.org/soap/envelope/"

    header: "JaarOpgaveClientPortTypeSendJaarOpgaveClientInput.Header | None" = field(
        default=None,
        metadata={
            "name": "Header",
            "type": "Element",
        },
    )
    body: "JaarOpgaveClientPortTypeSendJaarOpgaveClientInput.Body | None" = field(
        default=None,
        metadata={
            "name": "Body",
            "type": "Element",
        },
    )

    @dataclass
    class Header:
        header: Header | None = field(
            default=None,
            metadata={
                "name": "Header",
                "type": "Element",
                "namespace": "http://www.centric.nl/GWS/Header/v0300",
            },
        )

    @dataclass
    class Body:
        jaar_opgave_info: JaarOpgaveInfo | None = field(
            default=None,
            metadata={
                "name": "JaarOpgaveInfo",
                "type": "Element",
                "namespace": "http://www.centric.nl/GWS/Diensten/JaarOpgaveClient/v0400",
            },
        )


@dataclass
class JaarOpgaveClientPortTypeSendJaarOpgaveClientOutput:
    class Meta:
        name = "Envelope"
        namespace = "http://schemas.xmlsoap.org/soap/envelope/"

    header: "JaarOpgaveClientPortTypeSendJaarOpgaveClientOutput.Header | None" = field(
        default=None,
        metadata={
            "name": "Header",
            "type": "Element",
        },
    )
    body: "JaarOpgaveClientPortTypeSendJaarOpgaveClientOutput.Body | None" = field(
        default=None,
        metadata={
            "name": "Body",
            "type": "Element",
        },
    )

    @dataclass
    class Header:
        header: Header | None = field(
            default=None,
            metadata={
                "name": "Header",
                "type": "Element",
                "namespace": "http://www.centric.nl/GWS/Header/v0300",
            },
        )

    @dataclass
    class Body:
        jaar_opgave_info_response: JaarOpgaveInfoResponse | None = field(
            default=None,
            metadata={
                "name": "JaarOpgaveInfoResponse",
                "type": "Element",
                "namespace": "http://www.centric.nl/GWS/Diensten/JaarOpgaveClient/v0400",
            },
        )
        fault: "JaarOpgaveClientPortTypeSendJaarOpgaveClientOutput.Body.Fault | None" = field(
            default=None,
            metadata={
                "name": "Fault",
                "type": "Element",
            },
        )

        @dataclass
        class Fault:
            faultcode: str | None = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "",
                },
            )
            faultstring: str | None = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "",
                },
            )
            faultactor: str | None = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "",
                },
            )
            detail: "JaarOpgaveClientPortTypeSendJaarOpgaveClientOutput.Body.Fault.Detail | None" = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "",
                },
            )

            @dataclass
            class Detail:
                fwi: Fwi | None = field(
                    default=None,
                    metadata={
                        "name": "FWI",
                        "type": "Element",
                        "namespace": "http://www.centric.nl/GWS/FWI/v0200",
                    },
                )


class JaarOpgaveClientPortTypeSendJaarOpgaveClient:
    uri = "#JaarOpgaveClientPolicy"
    name = "SendJaarOpgaveClient"
    style = "document"
    location = "No target address"
    transport = "http://schemas.xmlsoap.org/soap/http"
    input = JaarOpgaveClientPortTypeSendJaarOpgaveClientInput
    output = JaarOpgaveClientPortTypeSendJaarOpgaveClientOutput
