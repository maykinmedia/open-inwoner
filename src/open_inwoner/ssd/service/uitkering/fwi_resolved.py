from dataclasses import dataclass, field
from typing import List, Optional

from open_inwoner.ssd.service.uitkering.fwi_include_resolved import Actor

__NAMESPACE__ = "http://www.centric.nl/GWS/FWI/v0200"


@dataclass
class NietsGevonden:
    class Meta:
        namespace = "http://www.centric.nl/GWS/FWI/v0200"

    any_element: Optional[object] = field(
        default=None,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
        },
    )


@dataclass
class Melding:
    code: Optional[str] = field(
        default=None,
        metadata={
            "name": "Code",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    tekst: Optional[str] = field(
        default=None,
        metadata={
            "name": "Tekst",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    detail: List[str] = field(
        default_factory=list,
        metadata={
            "name": "Detail",
            "type": "Element",
            "namespace": "",
        },
    )
    bron: Optional[Actor] = field(
        default=None,
        metadata={
            "name": "Bron",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class Fwi:
    class Meta:
        name = "FWI"
        namespace = "http://www.centric.nl/GWS/FWI/v0200"

    fout: List[Melding] = field(
        default_factory=list,
        metadata={
            "name": "Fout",
            "type": "Element",
            "namespace": "",
        },
    )
    waarschuwing: List[Melding] = field(
        default_factory=list,
        metadata={
            "name": "Waarschuwing",
            "type": "Element",
            "namespace": "",
        },
    )
    informatie: List[Melding] = field(
        default_factory=list,
        metadata={
            "name": "Informatie",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class Fout(Melding):
    class Meta:
        namespace = "http://www.centric.nl/GWS/FWI/v0200"
