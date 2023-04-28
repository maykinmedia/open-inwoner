from lxml.etree import ParseError, ParserError
from lxml.html import fragments_fromstring, tostring


def process_csp(context, data, namespace):
    """
    contextprocessor to add CSP nonce to (some) script tags in sekizai blocks
    usage:

    {% render_block "js"  postprocessor "open_inwoner.cms.csp.sekizai.process_csp" %}
    """
    request = context["request"]

    # TODO decide if we want staff-user filtering here
    if not request.user.is_authenticated or not request.user.is_staff:
        return data

    try:
        fragments = fragments_fromstring(data)
    except (ParseError, ParserError):
        return data
    for fragment in fragments:
        for elem in fragment.cssselect("script[data-cms]"):
            elem.set("nonce", str(request.csp_nonce))

    html = "\n".join(tostring(f, encoding="unicode") for f in fragments)
    return html
