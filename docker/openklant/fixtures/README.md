# Open Klant

Open Inwoner has an integration with the Klanten API and Contactmomenten API and this Docker
setup allows for more accurate local testing of this integration (using Open Klant)

## docker-compose

Start an Open Klant instance in your local environment from the parent directory:

```bash
docker-compose -f docker-compose.openklant.yml up -d
```

In order to allow access to Open Klant via the same hostname via the Open Inwoner backend
container and the browser, add the following entry to your `/etc/hosts` file:

```
127.0.0.1 openklant.local
```

## Load fixtures

To load some initial data to get set up quickly, run the following command

```bash
cat openklant/fixtures/db.json | docker exec -i docker-openklant-web-1 src/manage.py loaddata --format=json -
```

This creates an admin account (credentials: admin / `admin`) and creates a `Klant` object that is linked to
KvK number `68750110`, as well as a `ContactMoment` and `KlantContactMoment` linked to this `Klant`
