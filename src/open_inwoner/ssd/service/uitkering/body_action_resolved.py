from dataclasses import dataclass, field
from typing import Optional

from open_inwoner.ssd.service.uitkering.fwi_include_resolved import TypePeriode

__NAMESPACE__ = "http://www.centric.nl/GWS/Diensten/UitkeringsSpecificatieClient/v0600"


@dataclass
class Request:
    burger_service_nr: Optional[str] = field(
        default=None,
        metadata={
            "name": "BurgerServiceNr",
            "type": "Element",
            "namespace": "",
            "required": True,
            "length": 9,
            "pattern": r"\d*",
        },
    )
    periodenummer: Optional[str] = field(
        default=None,
        metadata={
            "name": "Periodenummer",
            "type": "Element",
            "namespace": "",
            "required": True,
            "length": 6,
            "pattern": r"[1-2][0-9]{3}(0[1-9]|1[0-2])",
        },
    )
    type_periode: Optional[TypePeriode] = field(
        default=None,
        metadata={
            "name": "TypePeriode",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class UitkeringsSpecificatieInfo(Request):
    class Meta:
        namespace = (
            "http://www.centric.nl/GWS/Diensten/UitkeringsSpecificatieClient/v0600"
        )
