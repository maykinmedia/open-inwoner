# Open Afval

Open Inwoner's "Mijn afval" page is backed by the
[Open Afval](https://github.com/maykinmedia/open-afval) API. This fixture seeds
a local instance with enough data to exercise that page for real.

## Contents

`db.json` holds:

- an admin account (admin / `admin`);
- the API token `data.yaml`'s `openafval-test` service authenticates with;
- one klant with BSN `111222333` -- the DigiD-mock `testuser`, the same BSN
  `docker/openklant/seed_conversations.py` seeds Open Klant against;
- two addresses, five containers (restafval/GFT/medisch afval at the first
  address, restafval/GFT at the second) and their ledigingen, fortnightly
  (monthly for medisch afval) from 2025-01-01 to 2026-08-31.

Log in locally with that BSN and open "Mijn afval" to see them, including the
chart, the year filter and the address filter.

## Load fixtures

`docker-compose.openafval.yml` already loads `db.json` on `up`. To reload it
manually:

```bash
cat docker/openafval/fixtures/db.json \
    | docker exec -i open-inwoner-openafval-web-1 src/manage.py loaddata --format=json -
```
