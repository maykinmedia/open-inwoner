from unittest import TestCase

from parameterized import parameterized

from ..xml import (
    calculate_loon_zvw,
    format_address,
    format_date,
    format_date_month_name,
    format_float_repr,
    format_name,
    get_column,
    get_sign,
)


class ParsingUtilsTest(TestCase):
    @parameterized.expand(
        [
            ("100", "28", "72"),
            ("", "", ""),
        ]
    )
    def test_calculate_loon_zvw(self, fiscalloon, vergoeding_premie_zvw, expected):
        res = calculate_loon_zvw(fiscalloon, vergoeding_premie_zvw)
        self.assertEqual(res, expected)

    @parameterized.expand(
        [
            ("642", "6,42"),
            ("60", "0,60"),
            ("", ""),
        ]
    )
    def test_format_float_repr(self, value, expected):
        res = format_float_repr(value)
        self.assertEqual(res, expected)

    @parameterized.expand(
        [
            ("Desolation Row", "42", "x", "Desolation Row 42 x"),
            ("Desolation Row", "42", "", "Desolation Row 42"),
            ("Desolation Row  ", "  42", " x ", "Desolation Row 42 x"),
            ("Desolation Row", "42", "", "Desolation Row 42"),
            ("Desolation Row", "42", "  ", "Desolation Row 42"),
        ]
    )
    def test_format_address(self, street_name, house_nr, house_letter, expected):
        res = format_address(street_name, house_nr, house_letter)
        self.assertEqual(res, expected)

    @parameterized.expand([("20230826", "26-08-2023"), ("", "")])
    def test_format_date(self, value, expected):
        res = format_date(value)
        self.assertEqual(res, expected)

    @parameterized.expand(
        [
            ("202305", "Mei 2023"),
            ("202306", "Juni 2023"),
            ("", ""),
        ]
    )
    def test_format_date_month_name(self, value, expected):
        res = format_date_month_name(value)
        self.assertEqual(res, expected)

    @parameterized.expand(
        [
            ("Johannes", "de", "Silentio", "J. de Silentio"),
            ("Johannes Maria Salvadore", "de la", "Mancha", "J. M. S. de la Mancha"),
            (
                "  Johannes Maria Salvadore",
                "de la  ",
                " Mancha ",
                "J. M. S. de la Mancha",
            ),
            ("Johannes", "", "Silentio", "J. Silentio"),
            ("Johannes", "  ", "Silentio", "J. Silentio"),
        ]
    )
    def test_format_name(self, first_name, voorvoegsel, last_name, expected):
        res = format_name(first_name, voorvoegsel, last_name)
        self.assertEqual(res, expected)

    @parameterized.expand(
        [
            ({"a": {"b": "-"}}, "a.b", "-"),
            ({"a": {"b": "+"}}, "a.b", ""),
            ({"a": {"b": ""}}, "a.b", ""),
        ]
    )
    def test_get_sign(self, target, spec, expected):
        res = get_sign(target, spec)
        self.assertEqual(res, expected)

    @parameterized.expand(
        [
            ("1", "plus"),
            ("2", "minus"),
            ("", "base"),
        ]
    )
    def test_get_column(self, value, expected):
        res = get_column(value)
        self.assertEqual(res, expected)
