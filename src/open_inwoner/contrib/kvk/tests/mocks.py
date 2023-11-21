simple = {
    "pagina": 1,
    "aantal": 1,
    "totaal": 1,
    "resultaten": [
        {
            "kvkNummer": "69599084",
            "vestigingsnummer": "000038509504",
            "handelsnaam": "Test EMZ Dagobert",
            "adresType": "bezoekadres",
            "straatnaam": "Abebe Bikilalaan",
            "plaats": "Amsterdam",
            "type": "hoofdvestiging",
            "links": [
                {
                    "rel": "basisprofiel",
                    "href": "https://api.kvk.nl/test/api/v1/basisprofielen/69599084",
                },
                {
                    "rel": "vestigingsprofiel",
                    "href": "https://api.kvk.nl/test/api/v1/vestigingsprofielen/000038509504",
                },
            ],
        },
    ],
}

multiple = {
    "pagina": 1,
    "aantal": 2,
    "totaal": 2,
    "resultaten": [
        {
            "kvkNummer": "69599084",
            "handelsnaam": "Test Stichting Bolderbast",
            "adresType": "bezoekadres",
            "straatnaam": "Oosterwal",
            "plaats": "Lochem",
            "type": "hoofdvestiging",
            "links": [
                {
                    "rel": "basisprofiel",
                    "href": "https://api.kvk.nl/test/api/v1/basisprofielen/69599068",
                }
            ],
        },
        {
            "kvkNummer": "69599084",
            "vestigingsnummer": "000038509504",
            "handelsnaam": "Test EMZ Dagobert",
            "adresType": "bezoekadres",
            "straatnaam": "Abebe Bikilalaan",
            "plaats": "Amsterdam",
            "type": "hoofdvestiging",
            "links": [
                {
                    "rel": "basisprofiel",
                    "href": "https://api.kvk.nl/test/api/v1/basisprofielen/69599084",
                },
                {
                    "rel": "vestigingsprofiel",
                    "href": "https://api.kvk.nl/test/api/v1/vestigingsprofielen/000038509504",
                },
            ],
        },
    ],
}
