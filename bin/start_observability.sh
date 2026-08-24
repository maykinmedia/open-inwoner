#!/bin/bash
#
# Bring up just the observability stack (Grafana/Loki/Prometheus/Promtail/
# Tempo/an OTel collector), without the rest of the app. See
# docs/installation/docker-compose.rst's "Testing OpenTelemetry Observability"
# section.
#
# Run from anywhere; this always operates from the repository root.

set -e

SCRIPT=$(readlink -f "$0")
REPO_ROOT=$(dirname "$(dirname "$SCRIPT")")
cd "$REPO_ROOT"

# docker/docker-compose.observability.yml's bind mounts (e.g.
# ./docker/observability/prometheus/prometheus.yml) are written relative to
# the repository root, matching every other satellite compose file (see
# bin/stack.sh's header comment) -- NOT relative to this file's own
# directory, which is what Compose would otherwise use as the "project
# directory" when it's the only `-f` file given. Pin it explicitly so this
# script and bin/stack.sh resolve those paths the same way.
docker compose --project-directory . -f docker/docker-compose.observability.yml up
