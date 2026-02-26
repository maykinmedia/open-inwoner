import json
import unittest
from pathlib import Path

from jsonschema import ValidationError as JSONSchemaValidationError, validate
from pydantic import ValidationError as PydanticValidationError

from open_inwoner.cms.plugins.api_models import (
    ExternFormulierTaakObject,
    ExternFormulierTaakRecord,
    UrlTaakObject,
    UrlTaakRecord,
)

# Load JSON schemas
EXTERN_FORMULIER_SCHEMA_PATH = (
    Path(__file__).parent.parent / "api_models" / "externe_formulier_taak.json"
)
with open(EXTERN_FORMULIER_SCHEMA_PATH) as f:
    EXTERN_FORMULIER_TAAK_SCHEMA = json.load(f)

URL_TAAK_SCHEMA_PATH = (
    Path(__file__).parent.parent / "api_models" / "url_taak_schema.json"
)
with open(URL_TAAK_SCHEMA_PATH) as f:
    URL_TAAK_SCHEMA = json.load(f)


# Valid test cases
VALID_EXTERN_FORMULIER_TAAK_RECORD = {
    "titel": "Test Taak",
    "status": "open",
    "soort": "externformulier",
    "verwerker_taak_id": "550e8400-e29b-41d4-a716-446655440000",
    "eigenaar": "OIP",
    "betrokkene": {
        "source": "digid",
        "levelOfAssurance": "urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract",
        "authorizee": {
            "legalSubject": {
                "identifierType": "bsn",
                "identifier": "123456789",
            }
        },
    },
    "portaalformulier": {
        "formulier": {
            "soort": "url",
            "value": "https://example.com/form",
        }
    },
}

VALID_EXTERN_FORMULIER_TAAK_RECORD_WITH_OPTIONALS = (
    VALID_EXTERN_FORMULIER_TAAK_RECORD
    | {
        "toelichting": "Dit is een toelichting",
        "doorlooptijd": "P14D",
        "verloopdatum": "2025-12-31T23:59:59Z",
        "koppeling": {
            "registratie": "zaak",
            "value": "450e8400-e29b-41d4-a716-446655440001",
        },
        "deadline_verlengbaar": True,
        "portaalformulier": {
            "formulier": {
                "soort": "url",
                "value": "https://example.com/form",
            },
            "data": {"volledige_naam": "Jan Jansen"},
            "verzonden_data": {"volledige_naam": "Jan Jansen"},
        },
    }
)

VALID_EXTERN_FORMULIER_TAAK_OBJECT = {
    "url": "https://objects-api.example.com/api/v1/objects/123",
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
} | {"record": VALID_EXTERN_FORMULIER_TAAK_RECORD}


# Invalid test cases for ExternFormulierTaakRecord
INVALID_MISSING_REQUIRED_FIELD = {
    # Missing 'titel'
    "status": "open",
    "soort": "externformulier",
    "verwerker_taak_id": "550e8400-e29b-41d4-a716-446655440000",
    "eigenaar": "OIP",
    "betrokkene": {
        "source": "digid",
        "levelOfAssurance": "urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract",
        "authorizee": {
            "legalSubject": {
                "identifierType": "bsn",
                "identifier": "123456789",
            }
        },
    },
    "portaalformulier": {
        "formulier": {
            "soort": "url",
            "value": "https://example.com/form",
        }
    },
}

INVALID_WRONG_STATUS = VALID_EXTERN_FORMULIER_TAAK_RECORD | {
    "status": "invalid_status",  # Not in allowed enum
}

INVALID_WRONG_BSN_LENGTH = VALID_EXTERN_FORMULIER_TAAK_RECORD | {
    "betrokkene": {
        "source": "digid",
        "levelOfAssurance": "urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract",
        "authorizee": {
            "legalSubject": {
                "identifierType": "bsn",
                "identifier": "12345",  # Too short, must be 9 digits
            }
        },
    },
}

INVALID_DOORLOOPTIJD_PATTERN = VALID_EXTERN_FORMULIER_TAAK_RECORD | {
    "doorlooptijd": "14D",  # Missing 'P' prefix
}

INVALID_KOPPELING_MISSING_VALUE = VALID_EXTERN_FORMULIER_TAAK_RECORD | {
    "koppeling": {
        "registratie": "zaak",
        # Missing 'value' field
    },
}

INVALID_UUID_FORMAT = VALID_EXTERN_FORMULIER_TAAK_RECORD | {
    "verwerker_taak_id": "not-a-valid-uuid",
}

INVALID_PORTAALFORMULIER_MISSING_FORMULIER = VALID_EXTERN_FORMULIER_TAAK_RECORD | {
    "portaalformulier": {
        "data": {"volledige_naam": "Jan Jansen"},
        # Missing 'formulier' field
    },
}


# UrlTaak test cases
VALID_URL_TAAK_RECORD = {
    "titel": "Check loan",
    "status": "open",
    "soort": "url",
    "verwerker_taak_id": "18af0b6a-967b-4f81-bb8e-a44988e0c2f0",
    "eigenaar": "gzac-sd",
    "identificatie": {
        "type": "bsn",
        "value": "123456789",
    },
    "url": {
        "uri": "https://example.com/task",
    },
}

VALID_URL_TAAK_RECORD_WITH_OPTIONALS = VALID_URL_TAAK_RECORD | {
    "verloopdatum": "2025-09-20T18:25:43.524Z",
    "koppeling": {
        "registratie": "zaak",
        "value": "5551a7c5-4e92-43e6-8d23-80359b7e22b7",
    },
    # Note: toelichting and doorlooptijd are in the Pydantic model but not in the JSON schema
}

VALID_URL_TAAK_RECORD_WITH_KVK = VALID_URL_TAAK_RECORD | {
    "identificatie": {
        "type": "kvk",
        "value": "12345678",
    },
}

VALID_URL_TAAK_OBJECT = {
    "url": "https://objects-api.example.com/api/v1/objects/456",
    "uuid": "18af0b6a-967b-4f81-bb8e-a44988e0c2f0",
} | {"record": VALID_URL_TAAK_RECORD}

# Invalid test cases for UrlTaakRecord
INVALID_URL_TAAK_MISSING_REQUIRED = {
    # Missing 'titel'
    "status": "open",
    "soort": "url",
    "verwerker_taak_id": "18af0b6a-967b-4f81-bb8e-a44988e0c2f0",
    "eigenaar": "gzac-sd",
    "identificatie": {
        "type": "bsn",
        "value": "123456789",
    },
    "url": {
        "uri": "https://example.com/task",
    },
}

INVALID_URL_TAAK_WRONG_STATUS = VALID_URL_TAAK_RECORD | {
    "status": "invalid_status",  # Not in allowed enum
}

INVALID_URL_TAAK_MISSING_URL = VALID_URL_TAAK_RECORD | {
    "url": {},  # Missing 'uri' field
}

INVALID_URL_TAAK_WRONG_BSN_LENGTH = VALID_URL_TAAK_RECORD | {
    "identificatie": {
        "type": "bsn",
        "value": "12345",  # Too short
    },
}

INVALID_URL_TAAK_WRONG_KVK_LENGTH = VALID_URL_TAAK_RECORD | {
    "identificatie": {
        "type": "kvk",
        "value": "123456",  # Too short, must be 8 digits
    },
}

INVALID_URL_TAAK_UUID_FORMAT = VALID_URL_TAAK_RECORD | {
    "verwerker_taak_id": "not-a-valid-uuid",
}


class ExternFormulierTaakRecordValidationTests(unittest.TestCase):
    """Test that ExternFormulierTaakRecord data validates correctly"""

    def test_validation(self):
        """Test both JSON schema and Pydantic validation for ExternFormulierTaakRecord"""
        test_cases = [
            # Format: (test_data, valid_for_json_schema, valid_for_pydantic, test_name)
            # Valid cases
            (VALID_EXTERN_FORMULIER_TAAK_RECORD, True, True, "valid_minimal"),
            (
                VALID_EXTERN_FORMULIER_TAAK_RECORD_WITH_OPTIONALS,
                True,
                True,
                "valid_with_optionals",
            ),
            # Invalid cases
            (INVALID_MISSING_REQUIRED_FIELD, False, False, "missing_required_field"),
            (INVALID_WRONG_STATUS, False, False, "wrong_status_value"),
            (
                INVALID_WRONG_BSN_LENGTH,
                False,
                True,
                "wrong_bsn_length",
            ),  # JSON schema checks, Pydantic accepts any digit string
            (
                INVALID_DOORLOOPTIJD_PATTERN,
                False,
                False,
                "invalid_doorlooptijd_pattern",
            ),
            (INVALID_KOPPELING_MISSING_VALUE, False, False, "koppeling_missing_value"),
            (
                INVALID_UUID_FORMAT,
                True,
                False,
                "invalid_uuid_format",
            ),  # JSON schema doesn't enforce, Pydantic does
            (
                INVALID_PORTAALFORMULIER_MISSING_FORMULIER,
                False,
                False,
                "missing_formulier",
            ),
        ]

        for test_data, valid_json, valid_pydantic, test_name in test_cases:
            with self.subTest(test_name=test_name):
                # Test JSON schema validation
                if valid_json:
                    validate(instance=test_data, schema=EXTERN_FORMULIER_TAAK_SCHEMA)
                else:
                    with self.assertRaises(JSONSchemaValidationError):
                        validate(
                            instance=test_data, schema=EXTERN_FORMULIER_TAAK_SCHEMA
                        )

                # Test Pydantic validation
                if valid_pydantic:
                    model = ExternFormulierTaakRecord.model_validate(test_data)
                    self.assertIsNotNone(model)
                else:
                    with self.assertRaises(PydanticValidationError):
                        ExternFormulierTaakRecord.model_validate(test_data)


class ExternFormulierTaakObjectValidationTests(unittest.TestCase):
    """Test that ExternFormulierTaakObject Pydantic model validates correctly"""

    def test_pydantic_validation(self):
        """Test Pydantic model validation for ExternFormulierTaakObject"""
        test_cases = [
            # Valid case
            (VALID_EXTERN_FORMULIER_TAAK_OBJECT, True, "valid_object"),
        ]

        for test_data, should_be_valid, test_name in test_cases:
            with self.subTest(test_name=test_name):
                if should_be_valid:
                    # Should not raise exception
                    model = ExternFormulierTaakObject.model_validate(test_data)
                    self.assertIsNotNone(model)
                    self.assertEqual(model.url, test_data["url"])
                    self.assertEqual(model.uuid, test_data["uuid"])
                    self.assertEqual(model.record.titel, test_data["record"]["titel"])
                else:
                    # Should raise validation error
                    with self.assertRaises(PydanticValidationError):
                        ExternFormulierTaakObject.model_validate(test_data)


class JSONSchemaAndPydanticConsistencyTests(unittest.TestCase):
    """Test consistency between JSON schema and Pydantic model validation"""

    def test_extern_formulier_json_schema_and_pydantic_model_consistency(self):
        """
        Test that valid data according to JSON schema is also valid for Pydantic model.

        Note: The JSON schema uses mixed casing (snake_case for top-level fields,
        camelCase for nested fields), while Pydantic's alias_generator applies uniformly.
        Therefore, we only test that JSON schema-valid data is accepted by Pydantic,
        not the reverse (Pydantic → dict → JSON schema validation).
        """
        # Data that passes JSON schema should also pass Pydantic validation
        test_cases = [
            ("minimal", VALID_EXTERN_FORMULIER_TAAK_RECORD),
            ("with_optionals", VALID_EXTERN_FORMULIER_TAAK_RECORD_WITH_OPTIONALS),
        ]

        for test_name, test_data in test_cases:
            with self.subTest(test_name=test_name):
                # Validate with JSON schema
                validate(instance=test_data, schema=EXTERN_FORMULIER_TAAK_SCHEMA)

                # Should also validate with Pydantic
                # Pydantic accepts the mixed casing via populate_by_name=True
                model = ExternFormulierTaakRecord.model_validate(test_data)
                self.assertIsNotNone(model)

    def test_url_taak_json_schema_and_pydantic_model_consistency(self):
        """
        Test that valid data according to URL Taak JSON schema is also valid for Pydantic model.
        """
        test_cases = [
            ("minimal", VALID_URL_TAAK_RECORD),
            ("with_optionals", VALID_URL_TAAK_RECORD_WITH_OPTIONALS),
            ("with_kvk", VALID_URL_TAAK_RECORD_WITH_KVK),
        ]

        for test_name, test_data in test_cases:
            with self.subTest(test_name=test_name):
                # Validate with JSON schema
                validate(instance=test_data, schema=URL_TAAK_SCHEMA)

                # Should also validate with Pydantic
                model = UrlTaakRecord.model_validate(test_data)
                self.assertIsNotNone(model)


class UrlTaakRecordValidationTests(unittest.TestCase):
    """Test that UrlTaakRecord data validates correctly"""

    def test_validation(self):
        """Test both JSON schema and Pydantic validation for UrlTaakRecord"""
        test_cases = [
            # Format: (test_data, valid_for_json_schema, valid_for_pydantic, test_name)
            # Valid cases
            (VALID_URL_TAAK_RECORD, True, True, "valid_minimal"),
            (VALID_URL_TAAK_RECORD_WITH_OPTIONALS, True, True, "valid_with_optionals"),
            (VALID_URL_TAAK_RECORD_WITH_KVK, True, True, "valid_with_kvk"),
            # Invalid cases
            (INVALID_URL_TAAK_MISSING_REQUIRED, False, False, "missing_required_field"),
            (INVALID_URL_TAAK_WRONG_STATUS, False, False, "wrong_status_value"),
            (INVALID_URL_TAAK_MISSING_URL, False, False, "missing_url_uri"),
            (
                INVALID_URL_TAAK_WRONG_BSN_LENGTH,
                True,
                False,
                "wrong_bsn_length",
            ),  # JSON schema pattern is lenient, Pydantic enforces exact length
            (
                INVALID_URL_TAAK_WRONG_KVK_LENGTH,
                True,
                False,
                "wrong_kvk_length",
            ),  # JSON schema pattern is lenient, Pydantic enforces exact length
            (
                INVALID_URL_TAAK_UUID_FORMAT,
                True,
                False,
                "invalid_uuid_format",
            ),  # JSON schema doesn't enforce, Pydantic does
        ]

        for test_data, valid_json, valid_pydantic, test_name in test_cases:
            with self.subTest(test_name=test_name):
                # Test JSON schema validation
                if valid_json:
                    validate(instance=test_data, schema=URL_TAAK_SCHEMA)
                else:
                    with self.assertRaises(JSONSchemaValidationError):
                        validate(instance=test_data, schema=URL_TAAK_SCHEMA)

                # Test Pydantic validation
                if valid_pydantic:
                    model = UrlTaakRecord.model_validate(test_data)
                    self.assertIsNotNone(model)
                else:
                    with self.assertRaises(PydanticValidationError):
                        UrlTaakRecord.model_validate(test_data)


class UrlTaakObjectValidationTests(unittest.TestCase):
    """Test that UrlTaakObject Pydantic model validates correctly"""

    def test_pydantic_validation(self):
        """Test Pydantic model validation for UrlTaakObject"""
        test_cases = [
            # Valid case
            (VALID_URL_TAAK_OBJECT, True, "valid_object"),
        ]

        for test_data, should_be_valid, test_name in test_cases:
            with self.subTest(test_name=test_name):
                if should_be_valid:
                    # Should not raise exception
                    model = UrlTaakObject.model_validate(test_data)
                    self.assertIsNotNone(model)
                    self.assertEqual(model.url, test_data["url"])
                    self.assertEqual(model.uuid, test_data["uuid"])
                    self.assertEqual(model.record.titel, test_data["record"]["titel"])
                else:
                    # Should raise validation error
                    with self.assertRaises(PydanticValidationError):
                        UrlTaakObject.model_validate(test_data)
