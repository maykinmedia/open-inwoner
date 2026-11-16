# Keycloak infrastructure

Open Inwoner supports OpenID Connect as an authentication protocol. Keycloak is
an example of an Identity Provider that supports OIDC.

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

**Realm**

The `test` realm's browser flow has the `Cookie` step disabled, so Keycloak
never silently reuses an existing SSO session: every login shows the
username/password form. This avoids being logged in as the previous test user
(e.g. the DigiD user when switching to eHerkenning) after quick successive
logins.

SSO sessions also expire after 5 seconds, just long enough for Open Inwoner to
exchange the authorization code. Otherwise Keycloak refuses a login as a
different user with "You are already authenticated as different user ... in this
session" for as long as the previous session lives.

**Clients**

- Client ID: `test-userinfo-jwt`, secret `ktGlGUELd1FR7dTXc84L7dJzUTjCtw9S`

  Configured to return the user info as a JWT rather than JSON response.

- Client ID: `testid`, secret: `7DB3KUAAizYCcmZufpHRVOcD0TOkNO3I`

**Users**

Every user's password is the same as its username.

The DigiD and eHerkenning users come in three classes: pre-registered ones (an
Open Inwoner user already exists, so login goes straight to the homepage), a
second pre-registered one to compare against, and "new" ones that no seeded user
or satellite service knows about, for walking through first-login registration
from a blank state. The pre-registered Open Inwoner users are loaded from
`docker/setup_configuration/fixtures/`; see the README there for those, and
`docker/open-zaak/fixtures/README.md` for which cases each user has in Open
Zaak.

DigiD (the `bsn` claim):

| User     | BSN         | Registered | Notes                                                                                                                             |
| -------- | ----------- | ---------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `bsn`    | `111222333` | yes        | The main citizen: all seeded demo data (cases, plans, messages, appointments, waste calendar, ...) hangs off this BSN.            |
| `bsn2`   | `123456782` | yes        | A second citizen, to check that one citizen does not see another's data.                                                          |
| `bsnnew` | `444555666` | no         | Unknown everywhere; registration starts with an empty form.                                                                       |
| `bsnbrp` | `999993847` | no         | Unknown to Open Inwoner, but present in the test set of the BRP mock (`personen-mock`), so registration is pre-filled from there. |

eHerkenning (the `legalSubjectID`, `actingSubjectID`, `name_qualifier`,
`service_id` and `service_uuid` attributes; branch users also have `vestiging`
and `representeeBSN`):

| User           | KvK        | Vestiging      | Registered | Notes                                                       |
| -------------- | ---------- | -------------- | ---------- | ----------------------------------------------------------- |
| `kvk`          | `68750110` | -              | yes        | Legal entity without a branch restriction (Test BV Donald). |
| `kvk2`         | `68727720` | -              | yes        | A second, unrelated company (Test NV Katrien).              |
| `vestiging`    | `68750110` | `000037178598` | yes        | Restricted to the main branch of the `kvk` company.         |
| `vestiging2`   | `68750110` | `000037178601` | yes        | Restricted to the other branch of the `kvk` company.        |
| `kvknew`       | `69599084` | -              | no         | Unknown to Open Inwoner and Open Zaak (Test EMZ Dagobert).  |
| `vestigingnew` | `69599084` | `000038509504` | no         | Same company as `kvknew`, with a branch restriction.        |

The KvK numbers are companies from the KvK sandbox, which Open Inwoner queries
for the company and branch name on login.

`bsn` and `bsnnew` also still have a `kvk` and a `legalSubjectID` attribute
(`12345678` and `87654321`), so they can log in through eHerkenning too; prefer
the dedicated users above.

Others:

- `digid-machtigen` / `digid-machtigen`, has the `aanvrager.bsn`,
  `gemachtigde.bsn` and `service_id` attributes (for DigiD machtigen)
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

The `bsn` client scope also exposes the eHerkenning attributes under the default
claim names of the eHerkenning OIDC configuration
(`urn:etoegang:core:LegalSubjectID`, `urn:etoegang:core:ActingSubjectID`,
`urn:etoegang:1.9:ServiceRestriction:Vestigingsnr` and `namequalifier`), so the
eHerkenning client works without overriding its claim paths.

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
