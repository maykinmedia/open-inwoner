# Open Klant

Open Inwoner has an integration with the Klanten API and Contactmomenten API and
this Docker setup allows for more accurate local testing of this integration
(using Open Klant)

## docker-compose

Start an Open Klant instance in your local environment from the parent
directory:

```bash
docker-compose -f docker-compose.openklant.yml up -d
```

In order to allow access to Open Klant via the same hostname via the Open
Inwoner backend container and the browser, add the following entry to your
`/etc/hosts` file:

```
127.0.0.1 openklant.local
```

## Load fixtures

`docker-compose.openklant.yml` already loads `db.json` on `up`. To reload it
manually:

```bash
cat openklant/fixtures/db.json | docker exec -i docker-openklant-web-1 src/manage.py loaddata --format=json -
```

This creates an admin account (admin / `admin`), the API token
`seed_conversations.py` uses, and a few base `klantinteracties.partij` records.
It also includes a batch of klantcontacten for BSN `111222333` (the DigiD-mock
`testuser`), seeded by running `python docker/openklant/seed_conversations.py`
against a running instance -- log in locally with that BSN and open "Mijn
vragen" to see them.
