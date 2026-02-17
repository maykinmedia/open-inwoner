"""
Pydantic validators for openklant_client types.

These validators are used in tests to validate API response data structures.
They wrap the types from openklant_client with Pydantic's TypeAdapter to provide
validation functionality similar to the validators that were previously included
in the vendored openklant2 package.
"""

from openklant_client.types.resources.klant_contact import KlantContact
from openklant_client.types.resources.onderwerp_object import OnderwerpObject
from openklant_client.types.resources.partij import Partij
from pydantic import TypeAdapter

# Create TypeAdapter validators for each resource type
KlantContactValidator = TypeAdapter(KlantContact)
OnderwerpObjectValidator = TypeAdapter(OnderwerpObject)
PartijValidator = TypeAdapter(Partij)
