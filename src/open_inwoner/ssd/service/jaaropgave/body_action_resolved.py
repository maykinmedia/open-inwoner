from dataclasses import dataclass, field

__NAMESPACE__ = "http://www.centric.nl/GWS/Diensten/JaarOpgaveClient/v0400"


@dataclass
class Request:
    burger_service_nr: str | None = field(
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
    dienstjaar: int | None = field(
        default=None,
        metadata={
            "name": "Dienstjaar",
            "type": "Element",
            "namespace": "",
            "required": True,
            "min_inclusive": 1980,
            "max_inclusive": 2999,
        },
    )


@dataclass
class JaarOpgaveInfo(Request):
    class Meta:
        namespace = "http://www.centric.nl/GWS/Diensten/JaarOpgaveClient/v0400"
