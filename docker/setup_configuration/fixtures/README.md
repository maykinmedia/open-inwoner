# Fixtures loaded alongside `setup_configuration`

Five unrelated things live here, all loaded by `bin/setup_configuration.sh`
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
  already use. The citizen has a real name and email, so `testuser` is
  pre-registered and skips the "necessary fields" form on first login. The
  Keycloak `newuser` (BSN `444555666`) has no counterpart here and starts blank;
- two `PlanTemplate`s ("Schuldhulpverlening", "Re-integratie naar werk"), each
  with two `ActionTemplate`s, so `collaborate:plan_choose_template` has
  something to offer;
- one open plan with three actions (one per `StatusChoices` value) and one
  finished plan, both with the begeleider and the citizen as `plan_contacts`;
- a short back-and-forth `Message` conversation between the same two users,
  backing the "Berichten" (inbox) page -- it has no satellite service either.

Log in via DigiD as `testuser`/`testuser` and open "Samenwerken" or "Berichten"
to see them.

## `acties.json`

Demo data for the "Openstaande acties" homepage plugin (`UserFeedPlugin`), which
-- like `samenwerken.json` -- has no satellite service of its own:
`FeedItemData` lives in Open Inwoner's own database. Not templated, for the same
reason as `samenwerken.json`. Loaded after `samenwerken.json`, since it
references the citizen user (pk `9002`) defined there.

Contents: three `message_simple` feed items for that same citizen, of the kind
normally created by `userfeed.hooks.common.simple_message()` for
development/debugging -- a profile-completion reminder, an appointment reminder,
and a new-message notification.

Log in via DigiD as `testuser`/`testuser` and open the homepage to see them
under "Openstaande acties".

## `notifications.json`

A `Subscription` (plus a placeholder `zgw_consumers.Service` for its required
`notifications_api_config`/NRC FK) for the ZGW notifications webhook at
`/api/openzaak/notifications/webhook/zaken`. There's no real Notifications API
in this stack, so nothing ever calls `Subscription.register()` against it --
this only exists so the webhook's JWT auth has a `client_id`/`secret` to
validate against. Not templated, for the same reason as `samenwerken.json`.

Use it with `manage.py send_mock_notification --resource status`, which
auto-discovers a real seeded zaak/status for BSN `111222333` and posts a
notification for it through the real webhook -- see that command's `--help` for
posting notifications for other zaken/resources, or generating malformed ones to
test rejection.

## `producten.json`

A minimal set of products and categories for the "Onderwerpen" page, which --
like `samenwerken.json` -- live in Open Inwoner's own database. Two root
categories ("Werk en inkomen" with a child "Schulden", and "Zorg en welzijn")
and three published products, each in one category. No images or content, so the
pages render without any filer files.

## Load fixtures manually

```bash
docker compose exec web src/manage.py loaddata /app/setup_configuration/fixtures/samenwerken.json
docker compose exec web src/manage.py loaddata /app/setup_configuration/fixtures/acties.json
docker compose exec web src/manage.py loaddata /app/setup_configuration/fixtures/notifications.json
docker compose exec web src/manage.py loaddata /app/setup_configuration/fixtures/producten.json
```

or, for `up --localhost`:

```bash
python src/manage.py loaddata docker/setup_configuration/fixtures/samenwerken.json
python src/manage.py loaddata docker/setup_configuration/fixtures/acties.json
python src/manage.py loaddata docker/setup_configuration/fixtures/notifications.json
python src/manage.py loaddata docker/setup_configuration/fixtures/producten.json
```
