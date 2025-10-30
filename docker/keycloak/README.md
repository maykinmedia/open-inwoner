# Keycloak infrastructure

Open Inwoner supports OpenID Connect as an authentication protocol. Keycloak is an
example of an Identity Provider that supports OIDC.

We include a compose stack for development and testing/CI purposes. This is
**NOT** suitable for production usage.

## docker compose

Start a Keycloak instance in your local environment from the parent directory:

```bash
docker compose -f docker-compose.keycloak.yml up -d
```

This brings up Keycloak, the admin interface is accessible at
http://localhost:8080/. You can now log in with the `admin`/`admin` credentials.

### Test data

**Clients**

- Client ID: `test-userinfo-jwt`, secret `ktGlGUELd1FR7dTXc84L7dJzUTjCtw9S`

  Configured to return the user info as a JWT rather than JSON response.

- Client ID: `testid`, secret: `7DB3KUAAizYCcmZufpHRVOcD0TOkNO3I`

**Users**

- `testuser` / `testuser`, has the `bsn`, `kvk`, `name_qualifier`,
  `legalSubjectID` and `actingSubjectID` attributes
- `digid-machtigen` / `digid-machtigen`, has the `aanvrager.bsn`,
  `gemachtigde.bsn` and `service_id` attributes (for DigiD machtigen)
- `eherkenning-bewindvoering` / `eherkenning-bewindvoering`, has the
  `legalSubjectID` (kvk), `actingSubjectID` (pseudo ID), `representeeBSN`,
  `service_id`, `service_uuid`, and `name_qualifier` attributes (for eHerkenning
  bewindvoering)
- `eherkenning-vestiging` / `eherkenning-vestiging`, has the `vestiging`
  attribute plus the attributes from `eherkenning-bewindvoering`.
- `admin` / `admin`, intended to create as django user (can be made staff). The
  email address is `admin@example.com`. Should get the `employeeId` claim (See
  below for how to add the custom claim).
- `eidas-person` / `eidas-person`, has the `person_bsn_identifier`,
  `first_name`, `family_name`, `birthdate`, `service_id` and `service_uuid`
  attributes (for eIDAS with natural person)
- `eidas-person-pseudo` / `eidas-person-pseudo`, has the
  `person_pseudo_identifier`, `first_name`, `family_name`, `birthdate`,
  `service_id` and `service_uuid` attributes (for eIDAS with natural person)
- `eidas-company` / `eidas-company`, has the `person_bsn_identifier`,
  `company_identifier`, `company_identifier_type`, `company_name`, `first_name`,
  `family_name`, `birthdate`, `service_id` and `service_uuid` attributes (for
  eIDAS with company)
- `eidas-company-pseudo` / `eidas-company-pseudo`, has the
  `person_bsn_identifier`, `company_identifier`, `company_identifier_type`,
  `company_name`, `first_name`, `family_name`, `birthdate`, `service_id` and
  `service_uuid` attributes (for eIDAS with company)

## Exporting the Realm

In short - exporting through the admin UI (rightfully) obfuscates client secrets
and user credentials. However, for reproducible builds/environments, we want to
include this data in the Realm export.

Ensure the service is up and running through docker-compose.

Ensure that UID `1000` can write to `./keycloak/import/`:

```bash
chmod o+rwx ./keycloak/import/
```

Then open another terminal and run:

```bash
docker compose -f docker-compose.keycloak.yml exec keycloak \
   /opt/keycloak/bin/kc.sh \
   export \
   --file /opt/keycloak/data/import/test-realm.json \
   --realm test
```
