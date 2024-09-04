# Open Klant 2 API Client

This Python package provides a client for interacting with Open Klant 2 services. It simplifies the process of making requests to the API and handling responses.

## Usage

```python
from openklant2 import OpenKlant2Client

client = OpenKlant2Client(api_root="https://openklant.maykin.nl/klantinteracties", token="your_api_token")

# Get user data
partijen = client.Partij.list()
print(partijen)
```

## Testing

### Re-recording VCR cassettes

The tests rely on VCR cassettes which are included in the repo. To dynamically create
an OpenKlant service and run the tests against it, run the following command:

```bash
$ cd src/openklant2
$ ./regenerate_vcr_fixtures.sh
```
