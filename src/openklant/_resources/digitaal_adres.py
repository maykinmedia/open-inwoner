from typing import Optional, TypedDict


class DigitaalAdresDetail(TypedDict):
    verstrektDoorBetrokkene: Optional[bool]
    verstrektDoorPartij: Optional[bool]
    soortDigitaalAdres: str
    adres: str
    omschrijving: str
