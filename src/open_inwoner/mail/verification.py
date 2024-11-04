from datetime import timedelta
from typing import TypedDict

from django.core import signing
from django.urls import reverse

from furl import furl
from mail_editor.helpers import find_template

from open_inwoner.accounts.models import User
from open_inwoner.utils.url import prepend_next_url_param


class BadToken(Exception):
    pass


VERIFY_SALT = "email_verify"
VERIFY_MAX_AGE = timedelta(hours=1)
VERIFY_GET_PARAM = "t"


class Payload(TypedDict):
    u: str
    e: str


def generate_email_verification_token(user: User) -> str:
    if not user.email:
        raise BadToken("user doesn't have email")
    if not user.is_active:
        raise BadToken("user not active")
    if user.email == user.verified_email:
        raise BadToken("already verified")

    payload: Payload = {
        "u": str(user.uuid),
        "e": user.email,
    }
    signer = signing.TimestampSigner(salt=VERIFY_SALT)
    token = signer.sign_object(payload, compress=True)
    return token


def decode_email_verification_token(token: str) -> Payload:
    signer = signing.TimestampSigner(salt=VERIFY_SALT)
    try:
        payload: Payload = signer.unsign_object(token, max_age=VERIFY_MAX_AGE)
    except signing.BadSignature:
        raise BadToken("invalid signature")
    else:
        return payload


def generate_email_verification_url(user: User) -> str:
    token = generate_email_verification_token(user)
    f = furl(reverse("mail:verification"))
    f.args[VERIFY_GET_PARAM] = token
    return f.url


def validate_email_verification_token(user: User, token: str) -> bool:
    # check condition
    if not user.is_authenticated:
        return False
    if not user.is_active or not user.email:
        return False

    # check payload
    try:
        payload = decode_email_verification_token(token)
    except BadToken:
        return False
    if not payload:
        return False
    if payload["u"] != str(user.uuid):
        return False
    if payload["e"] != user.email:
        return False

    # payload is good, let's apply it
    if user.verified_email != user.email:
        user.verified_email = payload["e"]
        user.save(update_fields=["verified_email"])

    return True


def send_user_email_verification_mail(user: User, next_url: str = None) -> bool:
    url = generate_email_verification_url(user)
    template = find_template("email_verification")
    if next_url:
        url = prepend_next_url_param(url, next_url)
    context = {
        "verification_link": url,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }
    template.send_email([user.email], context)
