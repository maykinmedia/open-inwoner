# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "flask>=3.1,<4",
# ]
# ///
"""
Mock for the Qmatic Orchestra Calendar API (open_inwoner.qmatic), covering
the two GETs Client.list_appointments_for_customer() makes (see
src/open_inwoner/qmatic/client.py), which is enough to exercise "Mijn
afspraken" end to end.

Customers are looked up by email in customers.json; any other email gets 404,
which the client treats as "no appointments". The client sends the logged-in
user's verified email, so customers.json's testuser@test.nl must match the
email/verified_email of the citizen in
docker/setup_configuration/fixtures/samenwerken.json (the user Keycloak's
DigiD testuser logs in as, by BSN). appointments.json is keyed
by customer publicId, and its __DAY_PLUS_N__/__DAY_MINUS_N__ placeholders are
replaced with dates relative to today on every request, since the client
drops appointments that start before today.

Run with `uv run server.py` (see docker/docker-compose.qmatic-mock.yml).
"""

import json
import re
from datetime import date, timedelta
from pathlib import Path

from flask import Flask, Response, abort, jsonify

FIXTURES_DIR = Path(__file__).parent
DAY_PLACEHOLDER = re.compile(r"__DAY_(PLUS|MINUS)_(\d+)__")

app = Flask(__name__)


def load_fixture(name: str):
    # Read on every request, so edits to the fixtures show up without a restart.
    return json.loads((FIXTURES_DIR / name).read_text())


def resolve_day(match: re.Match) -> str:
    sign = 1 if match.group(1) == "PLUS" else -1
    return (date.today() + timedelta(days=sign * int(match.group(2)))).isoformat()


@app.get("/appointment/customers/identify;email=<email>")
def identify_customer(email: str):
    customers = [
        customer
        for customer in load_fixture("customers.json")
        if customer["properties"]["email"] == email
    ]
    if not customers:
        abort(404)
    return jsonify(customers)


@app.get("/calendar-backend/public/api/v1/customers/<public_id>/appointments")
def list_appointments(public_id: str):
    appointments = load_fixture("appointments.json")
    if public_id not in appointments:
        abort(404)
    body = DAY_PLACEHOLDER.sub(resolve_day, json.dumps(appointments[public_id]))
    return Response(body, mimetype="application/json")


@app.get("/afspraak/<public_id>")
def booking_page(public_id: str):
    # QmaticConfig.booking_base_url: the "Wijzig of annuleer afspraak" link,
    # opened in the user's browser.
    return Response(
        f"Qmatic mock: here appointment {public_id} would be changed or cancelled.\n",
        mimetype="text/plain",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)  # noqa: S104
