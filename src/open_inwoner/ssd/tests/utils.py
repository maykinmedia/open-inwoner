import os
from pathlib import Path

from django.template.loader import render_to_string

from lxml import etree
from xsdata.formats.dataclass.context import XmlContext
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.handlers import LxmlEventHandler

SNAPSHOTS_DIR = Path(__file__).parent.resolve() / "snapshots"


def mock_get_report_info(path, info_response_node, info_type):  # pragma: no cover
    """
    Mock SOAP response content by retrieving XML data from files
    """
    with open(path, "rb") as f:
        tree = etree.parse(f)  # nosec
        node = tree.find(info_response_node)
        parser = XmlParser(context=XmlContext(), handler=LxmlEventHandler)
        res = parser.parse(node, info_type)
    return res


def get_component_value(componenthistorie, omschrijving):  # pragma: no cover
    """
    Retrieve the value ("waarde_bedrag") of a component from the
    componenthistorie by `omschrijving'
    """
    return next(
        item for item in componenthistorie if item.omschrijving == omschrijving
    ).bedrag.waarde_bedrag


def render_html(template_name, context, base_url=None, request=None):
    """
    Mock PDF rendering by returning the (unstyled) HTML instead
    """
    html_string = render_to_string(template_name, context, request)

    return html_string


def get_total_component_value(components: list, target: str) -> float:
    """
    Calculate the total value of all target components

    We retrieve the keys of rows together with their index from the list of components.
    The value (`str`) for each row is stored in the column with the next higher index
    (the components list has been filtered, hence we can assume that keys and values
    for each row are contiguous). Each value is formatted and converted to `float`
    before the sum is calculated.
    """
    # get component keys ("omschrijving") with index
    keys = [(key, components.index(key)) for key in components if key.text == target]

    # calculate sum of values of rows
    values = []
    for key, key_idx in keys:
        value_col = components[key_idx + 1]  # keys/values are contiguous
        value_string = value_col.text
        value = float(value_string.replace(",", "."))
        values.append(value)
    return sum(values)


class HTMLSnapshotMixin:
    """
    Compare rendered HTML against a snapshot stored in `SNAPSHOTS_DIR`.

    Run the tests with `UPDATE_SNAPSHOTS=1` to (re)write the snapshots instead, and
    review the resulting diff before committing it.
    """

    def assertHTMLMatchesSnapshot(self, html: str, name: str):
        path = SNAPSHOTS_DIR / f"{name}.html"

        if os.environ.get("UPDATE_SNAPSHOTS"):
            path.parent.mkdir(exist_ok=True)
            # strip whitespace like the pre-commit hooks do, so regenerating the
            # snapshots doesn't produce whitespace-only diffs
            lines = [line.rstrip() for line in html.splitlines()]
            path.write_text("\n".join(lines).rstrip("\n") + "\n")
            return

        if not path.exists():
            self.fail(
                f"Snapshot {path.name} does not exist, run the tests with "
                "UPDATE_SNAPSHOTS=1 to create it"
            )

        self.assertHTMLEqual(html, path.read_text())
