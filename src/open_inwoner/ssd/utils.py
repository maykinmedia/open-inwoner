from datetime import date

import dateutil


# TODO delete
def format_report_name(report_name: str) -> str:
    if report_name.isdigit():
        return f"{report_name}"
    parts = report_name.split("-")
    return f"{parts[0].capitalize()} {parts[1]}"


# TODO: delete
def convert_report_to_period(report_date: str) -> str:
    dt = dateutil.parser.parse(report_date)
    return dt.strftime("%Y%m")
