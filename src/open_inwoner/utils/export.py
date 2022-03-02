from django.contrib.staticfiles import finders
from django.template.loader import render_to_string

from weasyprint import CSS, HTML


def render_pdf(template_name, context, base_url=None, request=None) -> bytes:
    html_string = render_to_string(template_name, context, request)
    html = HTML(string=html_string, base_url=base_url)

    # add styling
    css_pdf_p = finders.find("bundles/pdf-p.css")
    css_web = finders.find("bundles/open_inwoner-css.css")
    return html.write_pdf(stylesheets=[CSS(css_pdf_p), CSS(css_web)])
