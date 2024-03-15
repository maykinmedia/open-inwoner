from datetime import datetime
from ipaddress import IPv4Address
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, HttpUrl, IPvAnyAddress, NonNegativeInt


class JSONEncoderMixin:
    # To make `BaseModel.dict()` produce JSON serialized data, i.e. for usage in tests
    # in tandem with `requests_mock`, we cast the data using the configured JSON encoders
    # Source: https://github.com/pydantic/pydantic/issues/1409#issuecomment-1381655025
    def _iter(self, **kwargs):
        for key, value in super()._iter(**kwargs):
            yield key, self.__config__.json_encoders.get(type(value), lambda v: v)(
                value
            )

    class Config:
        json_encoders = {
            # We need to specify a serializable format for datetimes and IPv4Addresses, otherwise
            # `BaseModel.dict()` will complain about certain types not being JSON serializable
            datetime: lambda dt: dt.isoformat(sep=" "),
            IPv4Address: str,
        }


class Members(BaseModel):
    active: NonNegativeInt
    unsubscribed: NonNegativeInt
    cleaned: NonNegativeInt


class LapostaList(JSONEncoderMixin, BaseModel):
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

    class Config(JSONEncoderMixin.Config):
        pass


class UserData(BaseModel):
    ip: IPvAnyAddress
    email: EmailStr
    source_url: HttpUrl | None
    custom_fields: dict | None
    options: dict | None


class Member(JSONEncoderMixin, BaseModel):
    member_id: str
    list_id: str
    email: EmailStr
    state: str | None = None
    signup_date: datetime | None = None
    ip: IPvAnyAddress
    source_url: HttpUrl | Literal[""] | None = None
    custom_fields: dict | None = None

    class Config(JSONEncoderMixin.Config):
        pass
