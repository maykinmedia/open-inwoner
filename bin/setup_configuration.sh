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
    # -- to specific values useful for visually testing case-visibility
    # rules. This fixture is a snapshot: it was produced by running
    # `zgw_import_data` for real against a stack seeded with
    # seed_openzaak_fixtures.py (see repository root), then hand-editing in
    # the OIP-only fields and `dumpdata`-ing the openzaak app's Config
    # models. Its URLs/UUIDs must match docker/open-zaak/fixtures/
    # open_zaak_fixtures.json's catalog rows -- if you regenerate one,
    # regenerate the other the same way.
    src/manage.py loaddata /app/setup_configuration/fixtures/openzaak_config.json

    mkdir -p "$MARKER_DIR"
    touch "$MARKER"
fi
