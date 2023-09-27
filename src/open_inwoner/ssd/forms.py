from datetime import date, datetime

from django import forms
from django.template.defaultfilters import date as django_date

from dateutil.relativedelta import relativedelta

from .models import SSDConfig


#
# utilities for retrieving download ranges
#
def get_monthly_report_dates() -> list[tuple[date, str]]:
    """Return choices of months for which reports are available for download"""

    config = SSDConfig.get_solo()

    if not config.maandspecificatie_enabled:
        return []

    today = datetime.today()
    month_range = config.maandspecificatie_delta

    dates = [today - relativedelta(months=i) for i in range(month_range)]

    available_from = config.maandspecificatie_available_from

    # check availability of report for current month
    if today.day < available_from:
        dates.pop(0)

    choices = []
    for report_date in dates:
        formatted = django_date(report_date, "M Y")
        choices.append((report_date.date(), formatted))

    return choices


def get_yearly_report_dates() -> list[tuple[date, str]]:
    """Return choices of years for which reports are available for download"""

    config = SSDConfig.get_solo()

    if not config.jaaropgave_enabled:
        return []

    today = datetime.today()
    year_range = config.jaaropgave_delta

    # `years=i+1` as the preceding year should be the first available
    dates = [today - relativedelta(years=i + 1) for i in range(year_range)]

    # parse date available
    available_from = datetime.strptime(
        config.jaaropgave_available_from, "%d-%m"
    ).replace(year=today.year)

    # check availability of report for preceding year
    if today < available_from:
        dates.pop(0)

    choices = []
    for report_date in dates:
        choices.append((report_date.date(), str(report_date.year)))

    return choices


#
# forms
#
class MonthlyReportsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["report_date"] = forms.DateTimeField(
            widget=forms.Select(choices=get_monthly_report_dates()),
            label="Toon uitkeringsspecificatie:",
        )

    def is_valid(self):
        try:
            dt = datetime.strptime(self.data["report_date"], "%Y-%m-%d").date()
        except ValueError:
            return False
        return any(dt in choice for choice in self.fields["report_date"].widget.choices)


class YearlyReportsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["report_date"] = forms.DateTimeField(
            widget=forms.Select(choices=get_yearly_report_dates()),
            label="Toon uitkeringsspecificatie:",
        )

    def is_valid(self):
        try:
            dt = datetime.strptime(self.data["report_date"], "%Y-%m-%d").date()
        except ValueError:
            return False
        return any(
            str(dt.year) in choice
            for choice in self.fields["report_date"].widget.choices
        )
