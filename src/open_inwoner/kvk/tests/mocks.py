empty = {
    "pagina": 1,
    "aantal": 0,
    "totaal": 0,
    "resultaten": [],
}

simple = {
    "pagina": 1,
    "aantal": 1,
    "totaal": 1,
    "resultaten": [
        {
            "kvkNummer": "68750110",
            "handelsnaam": "Test BV Donald",
            "type": "rechtspersoon",
            "links": [
                {
                    "rel": "basisprofiel",
                    "href": "https://api.kvk.nl/test/api/v1/basisprofielen/68750110",
                }
            ],
        }
    ],
}

multiple_branches = {
    "pagina": 1,
    "aantal": 2,
    "totaal": 2,
    "resultaten": [
        {
            "kvkNummer": "69599084",
            "vestigingsnummer": "028435810622",
            "handelsnaam": "Test Stichting Bolderbast",
            "adresType": "bezoekadres",
            "straatnaam": "Oosterwal",
            "plaats": "Lochem",
            "type": "hoofdvestiging",
            "links": [
                {
                    "rel": "basisprofiel",
                    "href": "https://api.kvk.nl/test/api/v1/basisprofielen/69599068",
                },
                {
                    "rel": "vestigingsprofiel",
                    "href": "https://api.kvk.nl/test/api/v1/vestigingsprofielen/028435810622",
                },
            ],
        },
        {
            "kvkNummer": "69599084",
            "vestigingsnummer": "000038509504",
            "handelsnaam": "Test Stichting Bolderbast",
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

basisprofiel_detail = {
    "kvkNummer": "68750110",
    "indNonMailing": "Ja",
    "naam": "Test BV Donald",
    "formeleRegistratiedatum": "20170519",
    "materieleRegistratie": {"datumAanvang": "20170519"},
    "totaalWerkzamePersonen": 1,
    "statutaireNaam": "Test BV Donald",
    "handelsnamen": [{"naam": "Test BV Donald", "volgorde": 0}],
    "sbiActiviteiten": [
        {
            "sbiCode": "01241",
            "sbiOmschrijving": "Teelt van appels en peren",
            "indHoofdactiviteit": "Ja",
        }
    ],
    "links": [
        {
            "rel": "self",
            "href": "https://api.kvk.nl/test/api/v1/basisprofielen/68750110",
        },
        {
            "rel": "vestigingen",
            "href": "https://api.kvk.nl/test/api/v1/basisprofielen/68750110/vestigingen",
        },
    ],
    "_embedded": {
        "hoofdvestiging": {
            "vestigingsnummer": "000037178598",
            "kvkNummer": "68750110",
            "formeleRegistratiedatum": "20200210",
            "materieleRegistratie": {"datumAanvang": "20140210"},
            "eersteHandelsnaam": "Test BV Donald",
            "indHoofdvestiging": "Ja",
            "indCommercieleVestiging": "Ja",
            "totaalWerkzamePersonen": 1,
            "adressen": [
                {
                    "type": "correspondentieadres",
                    "indAfgeschermd": "Nee",
                    "volledigAdres": "Postbus 200                                 1000AE Rommeldam",
                    "straatnaam": "Postbus",
                    "postcode": "1000AE",
                    "postbusnummer": 200,
                    "plaats": "Rommeldam",
                    "land": "Nederland",
                },
                {
                    "type": "bezoekadres",
                    "indAfgeschermd": "Nee",
                    "volledigAdres": "Hizzaarderlaan 3 A                                 8823SJ Lollum",
                    "straatnaam": "Hizzaarderlaan",
                    "huisnummer": 3,
                    "huisnummerToevoeging": "A",
                    "postcode": "8823SJ",
                    "plaats": "Lollum",
                    "land": "Nederland",
                },
            ],
            "links": [
                {
                    "rel": "self",
                    "href": "https://api.kvk.nl/test/api/v1/basisprofielen/68750110/hoofdvestiging",
                },
                {
                    "rel": "vestigingen",
                    "href": "https://api.kvk.nl/test/api/v1/basisprofielen/68750110/vestigingen",
                },
                {
                    "rel": "basisprofiel",
                    "href": "https://api.kvk.nl/test/api/v1/basisprofielen/68750110",
                },
                {
                    "rel": "vestigingsprofiel",
                    "href": "https://api.kvk.nl/test/api/v1/vestigingsprofielen/000037178598",
                },
            ],
        },
        "eigenaar": {
            "rsin": "857587973",
            "rechtsvorm": "Besloten vennootschap met gewone structuur",
            "uitgebreideRechtsvorm": "Besloten vennootschap met gewone structuur",
            "links": [
                {
                    "rel": "self",
                    "href": "https://api.kvk.nl/test/api/v1/basisprofielen/68750110/eigenaar",
                },
                {
                    "rel": "basisprofiel",
                    "href": "https://api.kvk.nl/test/api/v1/basisprofielen/68750110",
                },
            ],
        },
    },
}
