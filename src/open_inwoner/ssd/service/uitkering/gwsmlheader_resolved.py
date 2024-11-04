from dataclasses import dataclass, field

from xsdata.models.datatype import XmlDateTime

from open_inwoner.ssd.service.uitkering.fwi_include_resolved import Actor

__NAMESPACE__ = "http://www.centric.nl/GWS/Header/v0300"


@dataclass
class BerichtIdentificatie:
    dat_tijd_aanmaak_request: XmlDateTime | None = field(
        default=None,
        metadata={
            "name": "DatTijdAanmaakRequest",
            "type": "Element",
            "namespace": "",
        },
    )
    dat_tijd_ontvangst_request: XmlDateTime | None = field(
        default=None,
        metadata={
            "name": "DatTijdOntvangstRequest",
            "type": "Element",
            "namespace": "",
        },
    )
    dat_tijd_aanmaak_response: XmlDateTime | None = field(
        default=None,
        metadata={
            "name": "DatTijdAanmaakResponse",
            "type": "Element",
            "namespace": "",
        },
    )
    dat_tijd_ontvangst_response: XmlDateTime | None = field(
        default=None,
        metadata={
            "name": "DatTijdOntvangstResponse",
            "type": "Element",
            "namespace": "",
        },
    )
    applicatie_informatie: str | None = field(
        default=None,
        metadata={
            "name": "ApplicatieInformatie",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class RouteInformatie:
    bron: Actor | None = field(
        default=None,
        metadata={
            "name": "Bron",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    bestemming: Actor | None = field(
        default=None,
        metadata={
            "name": "Bestemming",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class Header:
    class Meta:
        namespace = "http://www.centric.nl/GWS/Header/v0300"

    route_informatie: RouteInformatie | None = field(
        default=None,
        metadata={
            "name": "RouteInformatie",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    bericht_identificatie: BerichtIdentificatie | None = field(
        default=None,
        metadata={
            "name": "BerichtIdentificatie",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
