import logging

from django.http import HttpResponse

from lxml.etree import ParseError, ParserError
from lxml.html import document_fromstring, tostring

logger = logging.getLogger(__name__)


class DjangoCMSCSPMiddleware:
    """
    middleware to add CSP nonce to (some) script tags
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response: HttpResponse = self.get_response(request)
        if response.streaming:
            return response

        if response.status_code != 200:
            return response

        content_type = response["Content-Type"].split(";")[0]
        if content_type != "text/html":
            return response

        # TODO decide if we want staff-user filtering here
        if not request.user.is_authenticated or not request.user.is_staff:
            return response

        csp_nonce = getattr(request, "csp_nonce", None)
        if not csp_nonce:
            logger.error("requires django-csp and response.csp_nonce")
            return response

        html_content = response.content.decode(response.charset)
        try:
            response.content = process_cms_csp(
                html_content, str(csp_nonce), response.charset
            )
        except (ParseError, ParserError):
            # what
            return response

        return response


def process_cms_csp(html, csp_nonce, encoding):
    tree = document_fromstring(html)

    for elem in tree.cssselect("script[data-cms]"):
        elem.set("nonce", csp_nonce)

    html = tostring(tree, encoding=encoding)
    return html
