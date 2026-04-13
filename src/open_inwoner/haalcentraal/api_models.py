import dataclasses
from datetime import date, datetime

from glom import GlomError, glom


@dataclasses.dataclass
class BRPData:
    # match with user model fields
    first_name: str = ""
    infix: str = ""
    last_name: str = ""

    street: str = ""
    housenumber: str = ""
    houseletter: str = ""
    housenumbersuffix: str = ""

    city: str = ""
    birthday: date | None = None

    # extra fields for My Data
    initials: str = ""
    birth_place: str = ""
    gender: str = ""
    postal_code: str = ""
    country: str = ""

    @classmethod
    def parse_date(
        cls, data: dict, path: str, default: date | None = None
    ) -> date | None:
        try:
            value = glom(data, path)
            return datetime.strptime(value, "%Y-%m-%d").date()
        except (GlomError, ValueError):
            return default

    def get_full_name(self) -> str:
        parts = (self.first_name, self.infix, self.last_name)
        return " ".join(v for v in parts if v)

    def get_housenumber(self):
        parts = []
        if self.housenumber:
            parts.append(str(self.housenumber))
        if self.houseletter:
            parts.append(str(self.houseletter))
        if self.housenumbersuffix:
            parts.append(" ")
            parts.append(str(self.housenumbersuffix))
        return "".join(parts)
