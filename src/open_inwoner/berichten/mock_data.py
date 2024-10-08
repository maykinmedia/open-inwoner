import uuid
from datetime import date
from open_inwoner.berichten.api_models import Bericht

MOCK_BERICHT_1 = {
    "onderwerp": "Besluit 1",
    "berichtTekst": "Hallo,\neen\nbericht 1",
    "publicatiedatum": date.fromisoformat("2024-01-01"),
    "referentie": "TODO",
    "handelingsperspectief": "TODO",
    "einddatumHandelingstermijn": date.fromisoformat("2024-12-01"),
    "geopend": False,
    "berichtType": "TODO",
    "identificatie": {"type": "bsn", "value": "999991954"},
    "bijlages": [
        "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
        "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/2",
    ],
}

MOCK_BERICHT_2 = {
    "onderwerp": "Voorbeeld onderwerp",
    "berichtTekst": "Goedendag,\nwederom een\n2e bericht",
    "publicatiedatum": date.fromisoformat("2024-01-02"),
    "referentie": "notificatie",
    "handelingsperspectief": "informatie ontvangen",
    "einddatumHandelingstermijn": date.fromisoformat("2024-12-02"),
    "geopend": False,
    "berichtType": "notificatie",
    "identificatie": {"type": "bsn", "value": "999991955"},
    "bijlages": [
        "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/3",
        "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/4",
    ],
}

MOCK_BERICHT_3 = {
    "onderwerp": "Betalen van uw parkeerbon",
    "berichtTekst": "Hallo,\neen\nbericht 3",
    "publicatiedatum": date.fromisoformat("2024-01-03"),
    "referentie": "TODO 3",
    "handelingsperspectief": "betalen",
    "einddatumHandelingstermijn": date.fromisoformat("2024-12-03"),
    "geopend": True,
    "berichtType": "betaalverzoek",
    "identificatie": {"type": "bsn", "value": "999991956"},
    "bijlages": [
        "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/5",
        "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/6",
    ],
}

MOCK_BERICHTEN = [
    Bericht.model_validate(MOCK_BERICHT_1 | {"object_uuid": str(uuid.uuid4())}),
    Bericht.model_validate(MOCK_BERICHT_2 | {"object_uuid": str(uuid.uuid4())}),
    Bericht.model_validate(MOCK_BERICHT_3 | {"object_uuid": str(uuid.uuid4())}),
]

MOCK_BERICHTEN *= (25 // len(MOCK_BERICHTEN)) + 1

# Slice
MOCK_BERICHTEN = MOCK_BERICHTEN[:25]
