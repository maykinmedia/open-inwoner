from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, HttpUrl, IPvAnyAddress, NonNegativeInt

from open_inwoner.utils.api import JSONEncoderMixin


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
