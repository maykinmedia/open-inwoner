from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, HttpUrl, IPvAnyAddress, NonNegativeInt


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


class UserData(BaseModel):
    ip: IPvAnyAddress
    email: EmailStr
    source_url: HttpUrl | None
    custom_fields: dict | None
    options: dict | None
