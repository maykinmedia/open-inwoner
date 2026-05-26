from open_inwoner.utils.api import APIError


class KlantAPIError(APIError):
    pass


class KlantAPIClientError(KlantAPIError):
    pass


class KlantAPIServerError(KlantAPIError):
    pass


class KlantAPIInvalidJSONError(KlantAPIError):
    pass


class KlantAPIDataError(KlantAPIError):
    pass


class KlantAPINetworkError(KlantAPIError):
    pass
