from .abstract import InclusionTagWebTest


class TestTable(InclusionTagWebTest):
    library = "table_tags"
    tag = "table"
    args = {
        "table_config": {
            "body": [
                {
                    "headers": [
                        {"text": "header cell"},
                    ],
                    "cells": [
                        {"text": "text cell 1"},
                        {"text": "text cell 2"},
                    ],
                },
                {
                    "headers": [
                        {"text": "header cell 1"},
                        {"text": "header cell 2"},
                    ],
                    "cells": [
                        {"text": "text cell"},
                    ],
                },
            ],
        }
    }

    def test_render(self):
        self.assertRender(self.args)

    def test_table_structure(self):
        self.assertSelector(".table", self.args)
        self.assertSelector(".table .table__body", self.args)
        self.assertSelector(".table .table__body .table__row:nth-child(1)", self.args)
        self.assertSelector(".table .table__body .table__row:nth-child(2)", self.args)
        self.assertSelector(
            ".table .table__body .table__row:nth-child(1) .table__header:nth-child(1)",
            self.args,
        )
        self.assertSelector(
            ".table .table__body .table__row:nth-child(1) .table__item:nth-child(2)",
            self.args,
        )
        self.assertSelector(
            ".table .table__body .table__row:nth-child(1) .table__item:nth-child(3)",
            self.args,
        )
        self.assertSelector(
            ".table .table__body .table__row:nth-child(2) .table__header:nth-child(1)",
            self.args,
        )
        self.assertSelector(
            ".table .table__body .table__row:nth-child(2) .table__header:nth-child(2)",
            self.args,
        )
        self.assertSelector(
            ".table .table__body .table__row:nth-child(2) .table__item:nth-child(3)",
            self.args,
        )

    def test_table_text(self):
        self.assertTextContent(
            ".table .table__body .table__row:nth-child(1) .table__header:nth-child(1)",
            "header cell",
            self.args,
        )
        self.assertTextContent(
            ".table .table__body .table__row:nth-child(1) .table__item:nth-child(2)",
            "text cell 1",
            self.args,
        )
        self.assertTextContent(
            ".table .table__body .table__row:nth-child(1) .table__item:nth-child(3)",
            "text cell 2",
            self.args,
        )
        self.assertTextContent(
            ".table .table__body .table__row:nth-child(2) .table__header:nth-child(1)",
            "header cell 1",
            self.args,
        )
        self.assertTextContent(
            ".table .table__body .table__row:nth-child(2) .table__header:nth-child(2)",
            "header cell 2",
            self.args,
        )
        self.assertTextContent(
            ".table .table__body .table__row:nth-child(2) .table__item:nth-child(3)",
            "text cell",
            self.args,
        )


class TestCaseTable(InclusionTagWebTest):
    library = "table_tags"
    tag = "case_table"
    args = {
        "case": {
            "initiator": "Case initiator",
            "type_description": "Case description",
            "result": "Case result",
            "end_date": "Case end date",
            "end_date_planned": "Case end date planned",
            "end_date_legal": "Case end date legal",
        }
    }

    def test_case_content(self):
        self.assertTextContent(
            ".table__row:nth-child(1) .table__header", "Aanvrager", self.args
        )
        self.assertTextContent(
            ".table__row:nth-child(1) .table__item", "Case initiator", self.args
        )

        self.assertTextContent(
            ".table__row:nth-child(2) .table__header", "Type", self.args
        )
        self.assertTextContent(
            ".table__row:nth-child(2) .table__item", "Case description", self.args
        )

        self.assertTextContent(
            ".table__row:nth-child(3) .table__header", "Resultaat", self.args
        )
        self.assertTextContent(
            ".table__row:nth-child(3) .table__item", "Case result", self.args
        )

        self.assertTextContent(
            ".table__row:nth-child(4) .table__header", "Einddatum", self.args
        )
        self.assertTextContent(
            ".table__row:nth-child(4) .table__item", "Case end date", self.args
        )

        self.assertTextContent(
            ".table__row:nth-child(5) .table__header", "Verwachte einddatum", self.args
        )
        self.assertTextContent(
            ".table__row:nth-child(5) .table__item", "Case end date planned", self.args
        )

        self.assertTextContent(
            ".table__row:nth-child(6) .table__header", "Wettelijke termijn", self.args
        )
        self.assertTextContent(
            ".table__row:nth-child(6) .table__item", "Case end date legal", self.args
        )
