GESPREKKEN_ROOT = "https://gesprekken.example.nl/api/v1/"
ZAAK_URL = "https://zaken.nl/api/v1/zaken/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
GESPREK_UUID = "11111111-1111-1111-1111-111111111111"
GESPREK_URL = f"{GESPREKKEN_ROOT}gesprekken/{GESPREK_UUID}"
PARTIJ_DEELNAME_UUID = "22222222-2222-2222-2222-222222222222"
ACTOR_DEELNAME_UUID = "33333333-3333-3333-3333-333333333333"
# References between resources are URLs
PARTIJ_DEELNAME = f"{GESPREKKEN_ROOT}gespreksdeelnames/{PARTIJ_DEELNAME_UUID}"
ACTOR_DEELNAME = f"{GESPREKKEN_ROOT}gespreksdeelnames/{ACTOR_DEELNAME_UUID}"
PARTIJ_UUID = "cccccccc-cccc-cccc-cccc-cccccccccccc"
PARTIJ = f"https://klantinteracties.example.nl/api/v1/partijen/{PARTIJ_UUID}"
FILE_ID = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"
BESTAND_URL = f"{GESPREKKEN_ROOT}bestanden/{FILE_ID}"
UPLOAD_URL = f"https://opslag.example.nl/uploads/{FILE_ID}?X-Amz-Signature=abc"
DOWNLOAD_URL = f"https://opslag.example.nl/downloads/{FILE_ID}?X-Amz-Signature=def"


def gesprek_detail(*, beeindigd: bool = False, bijdragen: list | None = None) -> dict:
    return {
        "uuid": GESPREK_UUID,
        "url": GESPREK_URL,
        "referentie": "G2026-00000001",
        "aanvangsmomentGesprek": "2026-06-12T09:00:00Z",
        "momentEindeGesprek": "2026-07-20T09:00:00Z" if beeindigd else None,
        "gespreksonderwerp": "Onderwerp van het gesprek",
        "aanleidingZaak": ZAAK_URL,
        "gespreksdeelnames": [
            {
                "uuid": PARTIJ_DEELNAME_UUID,
                "url": PARTIJ_DEELNAME,
                "gesprek": GESPREK_URL,
                "type": "partij",
                "partij": PARTIJ,
                "actor": None,
                "naam": "Piet",
                "aanvangsmomentDeelname": "2026-06-12T09:00:00Z",
                "momentEindeDeelname": None,
            },
            {
                "uuid": ACTOR_DEELNAME_UUID,
                "url": ACTOR_DEELNAME,
                "gesprek": GESPREK_URL,
                "type": "actor",
                "partij": None,
                "actor": "https://klantinteracties.example.nl/api/v1/actoren/medewerker",
                "naam": "M. Medewerker",
                "aanvangsmomentDeelname": "2026-06-12T09:00:00Z",
                "momentEindeDeelname": None,
            },
        ],
        "gespreksbijdragen": bijdragen
        if bijdragen is not None
        else [
            bijdrage(
                "44444444-4444-4444-4444-444444444444",
                PARTIJ_DEELNAME,
                "Mijn vraag",
                "2026-07-12T11:30:00Z",
            ),
            bijdrage(
                "55555555-5555-5555-5555-555555555555",
                ACTOR_DEELNAME,
                "Hartelijk dank voor uw bericht.",
                "2026-07-13T07:30:00Z",
            ),
        ],
    }


def bijdrage(
    uuid: str, verzender: str, tekst: str, moment: str, bijlagen: list | None = None
) -> dict:
    return {
        "uuid": uuid,
        "url": f"{GESPREKKEN_ROOT}gespreksbijdragen/{uuid}",
        "leveringsmoment": moment,
        "verzender": verzender,
        "tekstGespreksBijdrage": tekst,
        "gesprek": GESPREK_URL,
        "isReactieOp": None,
        "bijlagen": bijlagen or [],
    }


def bestand(status: str = "beschikbaar", **extra) -> dict:
    return {
        "fileId": FILE_ID,
        "url": BESTAND_URL,
        "bestandsnaam": "loonstrook.pdf",
        "bestandsomvang": 4,
        "contentType": "application/pdf",
        "status": status,
        "aangemaaktOp": "2026-07-13T07:30:00Z",
        **extra,
    }
