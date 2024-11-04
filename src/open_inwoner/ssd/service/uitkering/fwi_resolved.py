from dataclasses import dataclass, field

from open_inwoner.ssd.service.uitkering.fwi_include_resolved import Actor

__NAMESPACE__ = "http://www.centric.nl/GWS/FWI/v0200"


@dataclass
class NietsGevonden:
    class Meta:
        namespace = "http://www.centric.nl/GWS/FWI/v0200"

    any_element: object | None = field(
        default=None,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
        },
    )


@dataclass
class Melding:
    code: str | None = field(
        default=None,
        metadata={
            "name": "Code",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    tekst: str | None = field(
        default=None,
        metadata={
            "name": "Tekst",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    detail: list[str] = field(
        default_factory=list,
        metadata={
            "name": "Detail",
            "type": "Element",
            "namespace": "",
        },
    )
    bron: Actor | None = field(
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

    fout: list[Melding] = field(
        default_factory=list,
        metadata={
            "name": "Fout",
            "type": "Element",
            "namespace": "",
        },
    )
    waarschuwing: list[Melding] = field(
        default_factory=list,
        metadata={
            "name": "Waarschuwing",
            "type": "Element",
            "namespace": "",
        },
    )
    informatie: list[Melding] = field(
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
