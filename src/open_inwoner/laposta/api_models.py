from datetime import datetime
from ipaddress import IPv4Address
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, HttpUrl, IPvAnyAddress, NonNegativeInt

from open_inwoner.utils.time import convert_datetime_to_iso_8601_with_z_suffix


class Members(BaseModel):
    active: NonNegativeInt
    unsubscribed: NonNegativeInt
    cleaned: NonNegativeInt


class LapostaList(BaseModel):
    account_id: str
    list_id: str
    created: datetime
    modified: Any
    state: str
    name: str
    remarks: str
    subscribe_notification_email: EmailStr | Literal[""]
    unsubscribe_notification_email: EmailStr | Literal[""]
    account_id: str
    members: Members

    # Let `.dict()` handle JSON encoding
    # Source: https://github.com/pydantic/pydantic/issues/1409#issuecomment-1381655025
    def _iter(self, **kwargs):
        for key, value in super()._iter(**kwargs):
            yield key, self.__config__.json_encoders.get(type(value), lambda v: v)(
                value
            )

    class Config:
        json_encoders = {
            # custom output conversion for datetime
            datetime: convert_datetime_to_iso_8601_with_z_suffix
        }


class UserData(BaseModel):
    ip: IPvAnyAddress
    email: EmailStr
    source_url: HttpUrl | None
    custom_fields: dict | None
    options: dict | None


class Member(BaseModel):
    member_id: str
    list_id: str
    email: EmailStr
    state: str | None = None
    signup_date: datetime | None = None
    ip: IPvAnyAddress
    source_url: HttpUrl | Literal[""] | None = None
    custom_fields: dict | None = None

    # Let `.dict()` handle JSON encoding
    # Source: https://github.com/pydantic/pydantic/issues/1409#issuecomment-1381655025
    def _iter(self, **kwargs):
        for key, value in super()._iter(**kwargs):
            yield key, self.__config__.json_encoders.get(type(value), lambda v: v)(
                value
            )

    class Config:
        json_encoders = {
            # custom output conversion for datetime
            datetime: convert_datetime_to_iso_8601_with_z_suffix,
            IPv4Address: str,
        }
