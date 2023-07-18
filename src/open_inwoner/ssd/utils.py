import os

import dateutil
from weasyprint import HTML


def generate_pdf(file_url: str) -> bytes:
    with open(file_url, "r") as html_template:
        html_content = html_template.read()
        pdf_file = HTML(string=html_content).write_pdf()
        return pdf_file


def strip_extension(filename: str) -> str:
    """Return filename minus the extension"""

    parts = os.path.splitext(filename)
    return parts[0]


def convert_file_name_to_period(file_name):
    dt = dateutil.parser.parse(file_name)
    return dt.strftime("%Y%m")
