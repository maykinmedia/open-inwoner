from typing import List, TypedDict

from django import template
from django.utils.translation import gettext as _

from open_inwoner.components.utils import ContentsNode, parse_component_with_args

register = template.Library()


class TableCellConfig(TypedDict):
    text: str


class TableHeaderConfig(TypedDict):
    text: str


class TableRowConfig(TypedDict):
    headers: List[TableHeaderConfig]
    cells: List[TableCellConfig]


class TableConfig(TypedDict):
    body: List[TableRowConfig]


@register.inclusion_tag("components/table/table.html")
def table(table_config: TableConfig):
    return {"table": table_config}


@register.inclusion_tag("components/table/table.html")
def case_table(case: dict, **kwargs) -> dict:
    """
    Renders a table below the dashboard for additional values related to a Zaak (case).

    Usage:
        {% case_table case %}

    Variables:
        + case: dict | The case to be able to build the dashboard, fetching the documents and statusses of the case.

    Extra context:
        + table: TableConfig | The configuration of the table.
    """

    # build rows for data we actually have
    rows: List[TableRowConfig] = []

    def add_row_if_not_empty(key, label):
        value = case.get(key)
        if not value:
            return

        row = {"headers": [{"text": label}], "cells": [{"text": value}]}

        rows.append(row)

    add_row_if_not_empty("initiator", _("Aanvrager"))
    add_row_if_not_empty("type_description", _("Type"))
    add_row_if_not_empty("result", _("Resultaat"))
    add_row_if_not_empty("end_date", _("Einddatum"))
    add_row_if_not_empty("end_date_planned", _("Verwachte einddatum"))
    add_row_if_not_empty("end_date_legal", _("Wettelijke termijn"))

    table_config: TableConfig = {"body": rows}

    return {
        **kwargs,
        "table": table_config,
    }


@register.tag()
def render_table(parser, token):
    """
    Renders a table.

    Usage:
        {% render_table %}
        {% endrender_table %}

    Extra context:
        - contents: string (HTML) | this is the context between the render_table and endrender_table tags
    """
    bits = token.split_contents()
    context_kwargs = parse_component_with_args(parser, bits, "render_table")
    nodelist = parser.parse(("endrender_table",))
    parser.delete_first_token()
    return ContentsNode(
        nodelist, "components/table/render_table.html", **context_kwargs
    )


@register.tag()
def render_table_body(parser, token):
    """
    Renders a table body.

    Usage:
        {% render_table_body %}
        {% endrender_table_body %}

    Extra context:
        - contents: string (HTML) | this is the context between the render_table_body and endrender_table_body tags
    """
    bits = token.split_contents()
    context_kwargs = parse_component_with_args(parser, bits, "render_table_body")
    nodelist = parser.parse(("endrender_table_body",))
    parser.delete_first_token()
    return ContentsNode(nodelist, "components/table/table_body.html", **context_kwargs)


@register.tag()
def render_table_row(parser, token):
    """
    Renders a table row.

    Usage:
        {% render_table_row %}
        {% endrender_table_row %}

    Extra context:
        - contents: string (HTML) | this is the context between the render_table_row and endrender_table_row tags
    """
    bits = token.split_contents()
    context_kwargs = parse_component_with_args(parser, bits, "render_table_row")
    nodelist = parser.parse(("endrender_table_row",))
    parser.delete_first_token()
    return ContentsNode(nodelist, "components/table/table_row.html", **context_kwargs)


@register.tag()
def render_table_header(parser, token):
    """
    Renders a table row.

    Usage:
        {% render_table_header %}
        {% endrender_table_header %}

    Extra context:
        - contents: string (HTML) | this is the context between the render_table_header and endrender_table_header tags
    """
    bits = token.split_contents()
    context_kwargs = parse_component_with_args(parser, bits, "render_table_header")
    nodelist = parser.parse(("endrender_table_header",))
    parser.delete_first_token()
    return ContentsNode(
        nodelist, "components/table/table_header.html", **context_kwargs
    )


@register.tag()
def render_table_cell(parser, token):
    """
    Renders a table row.

    Usage:
        {% render_table_cell %}
        {% endrender_table_cell %}

    Extra context:
        - contents: string (HTML) | this is the context between the render_table_cell and endrender_table_cell tags
    """
    bits = token.split_contents()
    context_kwargs = parse_component_with_args(parser, bits, "render_table_cell")
    nodelist = parser.parse(("endrender_table_cell",))
    parser.delete_first_token()
    return ContentsNode(nodelist, "components/table/table_cell.html", **context_kwargs)
