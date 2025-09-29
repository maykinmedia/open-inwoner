# Open Klant 2 API Client

This Python package provides a client for interacting with Open Klant 2 services. It simplifies the process of making requests to the API and handling responses.

## Usage

```python
from openklant2 import OpenKlant2Client

client = OpenKlant2Client(api_root="https://openklant.maykin.nl/klantinteracties", token="your_api_token")

>>> partijen = client.Partij.list()
>>> partijen
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "uuid": "cfc8be25-3773-43b6-b394-455b7027b4c1",
      "url": "http://localhost:8338/klantinteracties/api/v1/partijen/cfc8be25-3773-43b6-b394-455b7027b4c1",
      "nummer": "0000000002",
      "soortPartij": "organisatie",
      "partijIdentificatie": {
        "naam": "Test Organisatie"
      }
    },
    {
      "uuid": "2a229e4e-f972-4ae5-a786-2dd21ed453d7",
      "url": "http://localhost:8338/klantinteracties/api/v1/partijen/2a229e4e-f972-4ae5-a786-2dd21ed453d7",
      "nummer": "0000000001",
      "soortPartij": "persoon",
      "partijIdentificatie": {
        "contactnaam": {
          "voorletters": "Dr.",
          "voornaam": "Test Persoon",
          "voorvoegselAchternaam": "Mrs.",
          "achternaam": "Gamble"
        }
      }
    }
  ]
}
```

## Testing

### Re-recording VCR cassettes

The tests rely on VCR cassettes which are included in the repo. To dynamically create
an OpenKlant service and run the tests against it, run the following command:

```bash
$ cd src/openklant2
$ ./regenerate_vcr_fixtures.sh
```
