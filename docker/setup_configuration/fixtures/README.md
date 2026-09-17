# Fixtures loaded alongside `setup_configuration`

Two unrelated things live here, both loaded by `bin/setup_configuration.sh`
right after `manage.py setup_configuration` (and mirrored in
`bin/stack.sh up --localhost`):

## `openzaak_config.json`

ZGW catalogue configuration -- `CatalogusConfig`/`ZaakTypeConfig`/
`ZaakType*TypeConfig` rows for the catalogue seeded by
`docker/open-zaak/fixtures/open_zaak_fixtures.json`. Generated from
`openzaak_config.json.j2`; do not hand-edit, run
`python bin/generate_setup_configuration.py` and commit the result instead.

## `samenwerken.json`

Demo data for the "Samenwerken" (collaborative planning) page, which has no
satellite service of its own -- `PlanTemplate`/`ActionTemplate`/`Plan`/`Action`
all live in Open Inwoner's own database, so unlike every other page there is
nothing for a `setup_configuration` step to point at a `Service`. Not templated:
it contains no service addresses, so the same file is used in Docker and host
mode.

Contents:

- two users who are each other's contact: a begeleider (`begeleider@user.nl` /
  `samenwerken`) and the citizen, keyed by BSN `111222333` -- the same BSN the
  DigiD-mock `testuser` logs in with, and that
  `docker/openklant/fixtures/db.json` and `docker/openafval/fixtures/db.json`
  already use;
- two `PlanTemplate`s ("Schuldhulpverlening", "Re-integratie naar werk"), each
  with two `ActionTemplate`s, so `collaborate:plan_choose_template` has
  something to offer;
- one open plan with three actions (one per `StatusChoices` value) and one
  finished plan, both with the begeleider and the citizen as `plan_contacts`.

Log in via DigiD as `testuser`/`testuser` and open "Samenwerken" to see them.

## Load fixtures manually

```bash
docker compose exec web src/manage.py loaddata /app/setup_configuration/fixtures/samenwerken.json
```

or, for `up --localhost`:

```bash
python src/manage.py loaddata docker/setup_configuration/fixtures/samenwerken.json
```
