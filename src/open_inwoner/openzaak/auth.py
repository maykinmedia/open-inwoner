import re

import jwt
from jwt import InvalidTokenError
from notifications_api_common.models import Subscription
from zds_client.auth import JWT_ALG

from open_inwoner.openzaak.exceptions import (
    NotificationAuthInvalid,
    NotificationAuthInvalidForClientID,
)


def get_valid_subscription_from_request(request) -> Subscription:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise NotificationAuthInvalid("missing Authorization header")
    return get_valid_subscriptions_from_header(auth_header)


def get_valid_subscriptions_from_header(header_value: str) -> Subscription:
    jwt_string = re.sub(r"^Bearer ", "", header_value)
    if not jwt_string:
        raise NotificationAuthInvalid("cannot locate Bearer token in header")
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
        raise NotificationAuthInvalid()

    if not client_id:
        raise NotificationAuthInvalid()

    qs = Subscription.objects.filter(client_id=client_id)
    for subscription in qs:
        try:
            jwt.decode(
                jwt_string,
                key=subscription.secret,
                algorithms=[JWT_ALG],
                options={"require": ["client_id"]},
                # iat (issued-at) could be ancient
                verify_iat=False,
            )
        except InvalidTokenError:
            continue
        else:
            return subscription

    # reaching here means we don't have a subscription for this client_id
    raise NotificationAuthInvalidForClientID(client_id)
