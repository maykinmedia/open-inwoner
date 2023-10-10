"""
Unit tests for the utility functions used in the reports forms
"""

from unittest import TestCase
from unittest.mock import patch

from freezegun import freeze_time

from ..forms import get_monthly_report_dates, get_yearly_report_dates
from .factories import SSDConfigFactory


class MonthlyChoicesTest(TestCase):
    @freeze_time("1985-01-25")
    @patch("open_inwoner.ssd.forms.SSDConfig.get_solo")
    def test_get_monthly_choices(self, mock_solo):
        mock_solo.return_value = SSDConfigFactory.build(
            maandspecificatie_delta=3,
            maandspecificatie_available_from=25,
        )

        choices = get_monthly_report_dates()

        self.assertEqual(len(choices), 3)

        date = choices[0][0]
        self.assertEqual(date.year, 1985)
        self.assertEqual(date.month, 1)

        date_repr = choices[0][1]
        self.assertEqual(date_repr, "Jan 1985")

    @freeze_time("1985-01-25")
    @patch("open_inwoner.ssd.forms.SSDConfig.get_solo")
    def test_current_month_not_yet_available(self, m):
        m.return_value = SSDConfigFactory.build(
            maandspecificatie_delta=3,
            maandspecificatie_available_from=29,
        )

        choices = get_monthly_report_dates()

        # range is 3, but current month not yet available, hence 2 results
        self.assertEqual(len(choices), 2)

        # most recent month should be one month before the current one
        date = choices[0][0]
        self.assertEqual(date.year, 1984)
        self.assertEqual(date.month, 12)

        date_repr = choices[0][1]
        self.assertEqual(date_repr, "Dec 1984")

    @patch("open_inwoner.ssd.forms.SSDConfig.get_solo")
    def test_monthly_reports_not_enabled(self, mock_solo):
        mock_solo.return_value = SSDConfigFactory.build(
            maandspecificatie_enabled=False,
        )

        res = get_monthly_report_dates()
        self.assertEqual(res, [])


class YearlyChoicesTest(TestCase):
    @freeze_time("1985-01-25")
    @patch("open_inwoner.ssd.forms.SSDConfig.get_solo")
    def test_get_yearly_choices(self, mock_solo):
        mock_solo.return_value = SSDConfigFactory.build(
            jaaropgave_delta=3,
            jaaropgave_available_from="25-01",
        )

        choices = get_yearly_report_dates()

        self.assertEqual(len(choices), 3)

        date = choices[0][0]
        self.assertEqual(date.year, 1984)
        self.assertEqual(date.month, 1)

        date_repr = choices[0][1]
        self.assertEqual(date_repr, "1984")

    @freeze_time("1985-01-25")
    @patch("open_inwoner.ssd.forms.SSDConfig.get_solo")
    def test_preceding_year_not_yet_available(self, m):
        m.return_value = SSDConfigFactory.build(
            jaaropgave_delta=3,
            jaaropgave_available_from="29-01",
        )

        choices = get_yearly_report_dates()

        # range is 3, but preceding year not yet available, hence 2 results
        self.assertEqual(len(choices), 2)

        # most recent year should be one year before the preceding one
        date = choices[0][0]
        self.assertEqual(date.year, 1983)
        self.assertEqual(date.month, 1)

        date_repr = choices[0][1]
        self.assertEqual(date_repr, "1983")

    @patch("open_inwoner.ssd.forms.SSDConfig.get_solo")
    def test_yearly_reports_not_enabled(self, mock_solo):
        mock_solo.return_value = SSDConfigFactory.build(
            jaaropgave_enabled=False,
        )

        res = get_yearly_report_dates()
        self.assertEqual(res, [])
