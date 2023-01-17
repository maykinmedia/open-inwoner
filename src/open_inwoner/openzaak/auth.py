import re

import jwt
from jwt import InvalidTokenError
from notifications_api_common.models import Subscription
from zds_client.auth import JWT_ALG

from open_inwoner.openzaak.exceptions import (
    InvalidAuth,
    InvalidAuthForClientID,
    NoSubscriptionForClientID,
)


def get_valid_subscription_from_request(request) -> Subscription:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise InvalidAuth("missing Authorization header")
    return get_valid_subscriptions_from_bearer(auth_header)


def get_valid_subscriptions_from_bearer(header_value: str) -> Subscription:
    jwt_string = re.sub(r"^Bearer ", "", header_value)
    if not jwt_string:
        raise InvalidAuth("cannot locate Bearer token in header")
    return get_valid_subscription_from_jwt(jwt_string)


def get_valid_subscription_from_jwt(jwt_string: str) -> Subscription:
    try:
        decoded_unverified = jwt.decode(
            jwt_string,
            algorithms=[JWT_ALG],
            options={
                "verify_signature": False,
                "require": ["client_id"],
            },
        )
        client_id = decoded_unverified.get("client_id")
    except InvalidTokenError:
        raise InvalidAuth("cannot decode token")

    if not client_id:
        raise InvalidAuth("missing 'client_id' in token")

    subscriptions_for_client_id = list(Subscription.objects.filter(client_id=client_id))
    if not subscriptions_for_client_id:
        raise NoSubscriptionForClientID(client_id)

    for subscription in subscriptions_for_client_id:
        try:
            jwt.decode(
                jwt_string,
                key=subscription.secret,
                algorithms=[JWT_ALG],
                options={
                    # iat (issued-at) could be ancient
                    "verify_iat": False,
                    "require": ["client_id"],
                },
            )
        except InvalidTokenError:
            continue
        else:
            return subscription

    raise InvalidAuthForClientID(client_id)
