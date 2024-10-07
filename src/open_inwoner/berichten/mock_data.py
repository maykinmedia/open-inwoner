import uuid

from open_inwoner.berichten.api_models import Bericht

MOCK_BERICHT = {
    "onderwerp": "Besluit",
    "berichtTekst": "Hallo\neen\nbericht",
    "publicatiedatum": "2024-01-01",
    "referentie": "TODO",
    "handelingsperspectief": "TODO",
    "geopend": False,
    "berichtType": "TODO",
    "identificatie": {"type": "bsn", "value": "999991954"},
    "bijlages": [
        "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
        "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/2",
    ],
}

MOCK_BERICHTEN = [
    Bericht.model_validate(MOCK_BERICHT | {"object_uuid": str(uuid.uuid4())})
    for _ in range(25)
]
