from open_inwoner.utils.api import APIError


class LapostaAPIError(APIError):
    pass


class LapostaAPIClientError(LapostaAPIError):
    pass


class LapostaAPIServerError(LapostaAPIError):
    pass


class LapostaAPIInvalidJSONError(LapostaAPIError):
    pass


class LapostaAPINetworkError(LapostaAPIError):
    pass
