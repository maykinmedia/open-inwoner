import os

from weasyprint import HTML


def generate_pdf(file_url: str) -> bytes:
    with open(file_url, "r") as html_template:
        html_content = html_template.read()
        pdf_file = HTML(string=html_content).write_pdf()
        return pdf_file


def get_filename_stem(filename: str) -> str:
    """Return filename minus the extension"""

    parts = os.path.splitext(filename)
    return parts[0]
