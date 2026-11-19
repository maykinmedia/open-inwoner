# Open Zaak fixtures

`open_zaak_fixtures.json` is mounted into the Open Zaak containers as
`/app/fixtures` (see `docker/docker-compose.open-zaak.yml`) and loaded when they
start. It holds the API credentials Open Inwoner connects with, one catalogus
with four zaaktypen, and the cases (zaken) below.

## Cases per test user

The users are the Keycloak test users from `docker/keycloak/README.md`. A user
"has" a case when it has a rol on it; whether Open Inwoner then shows the case
still depends on the confidentiality level and zaaktype configuration, which is
what the `SEED-INTERN`, `SEED-VERTROUWELIJK` and `SEED-GEEN-INFORMEREN` cases
are for.

| Cases (`omschrijving`)                                                                                 | Identificatie               | Users that have them |
| ------------------------------------------------------------------------------------------------------ | --------------------------- | -------------------- |
| `SEED-VISIBLE`, `SEED-VISIBLE (finished)`, `SEED-INTERN`, `SEED-VERTROUWELIJK`, `SEED-GEEN-INFORMEREN` | `TESTZAAK-*`                | `bsn`                |
| `SEED-VISIBLE`, `SEED-VISIBLE (finished)`                                                              | `TESTZAAK-BSN2-*`           | `bsn2`               |
| `SEED-VISIBLE`, `SEED-VISIBLE (finished)`                                                              | `TESTZAAK-KVK-*`            | `kvk`, `vestiging`   |
| `SEED-INTERN`, `SEED-VERTROUWELIJK`, `SEED-GEEN-INFORMEREN`                                            | `TESTZAAK-KVK-*`            | `kvk`                |
| `SEED-VESTIGING` for vestiging `000037178598`                                                          | `TESTZAAK-KVK-000037178598` | `kvk`, `vestiging`   |
| `SEED-VESTIGING` for vestiging `000037178601`                                                          | `TESTZAAK-KVK-000037178601` | `kvk`, `vestiging2`  |
| `SEED-VISIBLE`, `SEED-VISIBLE (finished)`                                                              | `TESTZAAK-KVK2-*`           | `kvk2`               |

`bsnnew`, `bsnbrp`, `kvknew` and `vestigingnew` have no cases.

## How the roles are modelled

- A citizen is the initiator, as a rol with betrokkeneType `natuurlijk_persoon`
  and their BSN.
- A company is the initiator, as a rol with betrokkeneType
  `niet_natuurlijk_persoon` with its RSIN (`innNnpId`) and KvK number. The stack
  fetches eHerkenning cases by RSIN (`fetch_eherkenning_zaken_with_rsin` in
  `docker/setup_configuration/data.yaml`), so the RSIN here must match the
  `rsin` of the pre-registered users in
  `docker/setup_configuration/fixtures/eherkenning.json`.
- A branch is a second rol on the same case, the mede-initiator, with
  betrokkeneType `vestiging` and its vestigingsnummer.

A user logged in for a branch only gets the cases that have both the company's
rol and a rol for that branch. A case that only a branch login sees is therefore
not possible: a branch's cases are always a subset of the company's.

Use `manage.py send_mock_notification` in Open Inwoner to post a notification
for one of these cases; see `docker/setup_configuration/fixtures/README.md`.
