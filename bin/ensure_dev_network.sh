#!/bin/bash
#
# Idempotently create the `open-inwoner-dev` Docker network used by the root
# docker-compose.yml and every satellite compose file under docker/
# (open-zaak, objects-apis, hc-brp-mock, openklant, keycloak, observability).
#
# All of those files attach to this network as `external: true` rather than
# creating it themselves, so that combining several of them in one `docker
# compose` invocation (or running them as separate `up` commands) never races
# over which one "owns" it -- see docs/installation/docker-compose.rst.
#
# Run this once before bringing up any stack for the first time. Safe to
# re-run; it's a no-op if the network already exists. `bin/stack.sh up` calls
# this for you.

set -e

NETWORK_NAME="open-inwoner-dev"

if docker network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
    echo "Network '$NETWORK_NAME' already exists."
else
    echo "Creating network '$NETWORK_NAME'..."
    docker network create "$NETWORK_NAME"
fi
