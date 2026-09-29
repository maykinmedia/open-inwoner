#!/bin/bash

# setup initial configuration using environment variables
# Run this script from the root of the repository

set -e

# Figure out abspath of this script
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

${SCRIPTPATH}/wait_for_db.sh

src/manage.py migrate

# `setup_configuration` steps like OpenZaakConfigurationStep and
# KlantenSysteemConfigurationStep converge fields back to whatever data.yaml
# says on every run (see their docstrings), overwriting any changes made
# through the admin in the meantime. That's fine for a first run against a
# fresh database, but not for every subsequent `docker compose up`/restart of
# an already-configured dev environment. Only run it once per database: a
# marker in a persistent volume (mounted only into this container, see
# docker-compose.yml) records that it already ran.
MARKER_DIR=${SETUP_CONFIGURATION_STATE_DIR:-/var/lib/open-inwoner/setup-configuration}
MARKER="${MARKER_DIR}/.completed"

if [ -f "$MARKER" ]; then
    echo "setup_configuration already completed previously (marker: $MARKER); skipping."
    echo "Remove that file, or the setup_configuration_state volume, to force a re-run."
else
    src/manage.py setup_configuration \
        --yaml-file /app/setup_configuration/data.yaml

    # CatalogusConfig/ZaakTypeConfig/ZaakType*TypeConfig are normally
    # populated by the `zgw_import_data` management command (also run daily
    # via Celery beat, see CELERY_BEAT_SCHEDULE in conf/base.py), which
    # discovers catalog data from the ZGW APIs live and upserts by
    # url/identificatie. We load a fixture instead of running that command
    # here, because it also pins fields the importer never touches --
    # notify_status_changes, document_upload_enabled, status_indicator, etc.
    src/manage.py loaddata /app/setup_configuration/fixtures/openzaak_config.json

    # Demo data for the "Samenwerken" page -- it has no satellite service of its
    # own, so there's no setup_configuration step to seed it through. The
    # citizen (pk 9002) is keyed by BSN, so first delete any other user with
    # that BSN (e.g. a DigiD-mock testuser from an earlier login); otherwise
    # loading it would create a duplicate and break BSN lookups.
    src/manage.py shell -c "
from django.db import transaction
from open_inwoner.accounts.models import User
with transaction.atomic():
    User.objects.filter(bsn='111222333').exclude(pk=9002).delete()
"
    src/manage.py loaddata /app/setup_configuration/fixtures/samenwerken.json

    # Demo data for the "Openstaande acties" homepage plugin. Loaded after
    # samenwerken.json, which it references the citizen user from.
    src/manage.py loaddata /app/setup_configuration/fixtures/acties.json

    # A Subscription (+ its placeholder NRC Service) to authenticate against
    # the ZGW notifications webhook with -- there's no real Notifications API
    # in this stack, so nothing ever calls Subscription.register(); this only
    # exists so `manage.py send_mock_notification` has something to sign a
    # JWT against. See docker/setup_configuration/fixtures/README.md.
    src/manage.py loaddata /app/setup_configuration/fixtures/notifications.json

    mkdir -p "$MARKER_DIR"
    touch "$MARKER"
fi
