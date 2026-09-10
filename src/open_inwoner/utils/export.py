from django.template.loader import render_to_string

from maykin_common.pdf import render_to_pdf


def render_pdf(template_name, context, request=None) -> bytes:
    html_string = render_to_string(template_name, context, request)
    _, pdf = render_to_pdf(html_string)
    return pdf
