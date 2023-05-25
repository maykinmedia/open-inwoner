import dataclasses
from datetime import date
from typing import Optional

from open_inwoner.accounts.models import User


@dataclasses.dataclass
class BRPData:
    # match with user model fields
    first_name: str = ""
    infix: str = ""
    last_name: str = ""
    street: str = ""
    housenumber: str = ""
    city: str = ""
    birthday: Optional[date] = None

    # extra fields
    # TODO rename birthday_city
    initials: str = ""
    birthday_city: str = ""
    gender: str = ""
    # TODO rename postcode to postal_code
    postcode: str = ""
    # TODO rename land to country
    country: str = ""

    def copy_to_user(self, user: User):
        # not all BRP fields are present on our User
        user.first_name = self.first_name
        user.infix = self.infix
        user.last_name = self.last_name
        user.street = self.street
        user.housenumber = self.housenumber
        user.city = self.city
        user.birthday = self.birthday
