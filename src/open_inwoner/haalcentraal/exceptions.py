from open_inwoner.utils.api import APIError


class BRPAPIError(APIError):
    pass


class BRPAPIClientError(BRPAPIError):
    pass


class BRPAPIServerError(BRPAPIError):
    pass


class BRPAPIInvalidJSONError(BRPAPIError):
    pass


class BRPAPINetworkError(BRPAPIError):
    pass
