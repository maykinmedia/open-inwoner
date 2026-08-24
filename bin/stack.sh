#!/bin/bash
#
# Manage the full local Open Inwoner stack: the main app plus every
# satellite service it talks to (Keycloak for OIDC, Open Zaak, the
# Objects/Objecttypes APIs, the Haal Centraal BRP mock, Open Klant, and Open
# Afval), plus the observability stack (Grafana/Loki/Prometheus/otel-collector).
#
# Usage:
#   bin/stack.sh up            # bring everything up: network, then satellites
#                               # (waited on until healthy), then the app
#   bin/stack.sh up --logs     # ...then follow the main app's logs
#   bin/stack.sh down          # stop and remove containers, keep volumes/data
#   bin/stack.sh down -v       # ...and remove volumes too (wipes all data)
#   bin/stack.sh urls          # print the service URLs shown at the end of `up`
#   bin/stack.sh logs [args]   # forwarded to `docker compose logs`
#   bin/stack.sh <cmd> [args]  # anything else forwarded to `docker compose`,
#                               # e.g. `bin/stack.sh ps`, `bin/stack.sh exec web bash`
#
# Run from anywhere; this always operates from the repository root.
#
# web-init's setup_configuration run needs Keycloak (OIDC discovery) and the
# ZGW/Open Klant services reachable, which is why `up` waits for those before
# starting the app. See docs/installation/docker-compose.rst for the full
# explanation and how to bring stacks up individually.

set -e

SCRIPT=$(readlink -f "$0")
REPO_ROOT=$(dirname "$(dirname "$SCRIPT")")
cd "$REPO_ROOT"

# docker-compose.dev.yml pulls in docker-compose.yml (the main app stack) and
# docker/docker-compose.keycloak.yml (OIDC) via `include:`, which resolves
# each file's relative paths against its own directory -- required for
# Keycloak's realm fixture mount to resolve correctly. The remaining
# satellite files use paths relative to the repository root instead, which
# works fine alongside `include:` since they're passed as plain `-f` files.
# See docker-compose.dev.yml's header comment for the full reasoning.
#
# `--project-directory .` pins that repository-root resolution explicitly,
# rather than relying on `docker-compose.dev.yml` happening to be the first
# `-f` file (Compose otherwise derives the project directory from whichever
# file is listed first).
COMPOSE=(
    docker compose
    --project-directory .
    -f docker-compose.dev.yml
    -f docker/docker-compose.open-zaak.yml
    -f docker/docker-compose.objects-apis.yml
    -f docker/docker-compose.hc-brp-mock.yml
    -f docker/docker-compose.openklant.yml
    -f docker/docker-compose.openafval.yml
    -f docker/docker-compose.observability.yml
)

print_urls() {
    cat <<'EOF'
  Open Inwoner              http://localhost:8000/        (behind nginx: http://localhost:9000/)
  Open Inwoner admin        http://localhost:8000/admin/  (click "Login with OIDC", Keycloak admin / admin)
  Mailpit (sent emails)     http://localhost:8025/
  Keycloak admin            http://localhost:8080/         (admin / admin)
  Open Zaak admin           http://localhost:8002/admin/   (admin / admin)
  Objecttypes API admin     http://localhost:8003/admin/   (admin / admin)
  Objects API admin         http://localhost:8004/admin/   (admin / admin)
  Open Klant admin          http://localhost:8338/admin/   (admin / admin)
  Open Afval admin          http://localhost:8339/admin/
  Haal Centraal BRP mock    http://localhost:5010/
  Grafana (observability)   http://localhost:3000/
  Prometheus                http://localhost:9090/
  Loki                      http://localhost:3100/ready

  DigiD login               http://localhost:8000/digid-oidc/authenticate/
  eHerkenning login         http://localhost:8000/eherkenning-oidc/authenticate/
  eIDAS login               http://localhost:8000/eidas-oidc/authenticate/
  (any Keycloak test user works -- see docker/keycloak/README.md for the
  full list, including DigiD machtigen and eHerkenning bewindvoering/vestiging)
EOF
}

cmd=${1:-}
[ $# -gt 0 ] && shift

case "$cmd" in
    up)
        echo "==> Ensuring the shared open-inwoner-dev network exists"
        bin/ensure_dev_network.sh

        echo
        echo "==> Starting satellite services (Keycloak, Open Zaak, Objects APIs, Haal Centraal BRP mock, Open Klant, Open Afval)"
        echo "    web-init needs all of these reachable, so they come up -- and are waited on -- first."
        "${COMPOSE[@]}" up -d --wait \
            keycloak \
            openzaak-web openzaak-celery \
            objecttypes-web objects-web objects-celery \
            personen-mock \
            openklant-seed \
            openafval-seed

        echo
        echo "==> Starting the main app stack (web-init will now configure it against the services above)"
        # OTEL_SDK_DISABLED defaults to true in docker-compose.yml's shared
        # x-app-env (so plain `docker compose up` stays opt-in, per
        # docs/installation/docker-compose.rst) -- overridden here since this
        # script also brings up the observability stack itself, and running
        # Grafana/Loki/Prometheus with nothing feeding them defeats the point.
        OTEL_SDK_DISABLED=false "${COMPOSE[@]}" up -d

        echo
        echo "==> Stack is up."
        echo
        print_urls
        echo
        echo "Bring it all down again with:"
        echo "  bin/stack.sh down"

        if [ "$1" = "--logs" ]; then
            "${COMPOSE[@]}" logs -f web web-init
        fi
        ;;

    urls)
        print_urls
        ;;

    down)
        echo "==> Stopping and removing containers"
        "${COMPOSE[@]}" down --remove-orphans "$@"
        echo
        echo "The shared open-inwoner-dev network is left in place (it's external to"
        echo "every compose file here). Remove it yourself if you need to, with:"
        echo "  docker network rm open-inwoner-dev"
        ;;

    reset-config)
        # web-init is a one-shot container, not a running service, so its
        # marker (see bin/setup_configuration.sh) can't be removed with
        # `exec` -- use a throwaway container against the same volume instead.
        echo "==> Clearing the setup_configuration marker"
        "${COMPOSE[@]}" run --rm --entrypoint sh web-init -c \
            "rm -f /var/lib/open-inwoner/setup-configuration/.completed"

        echo
        echo "==> Re-running web-init"
        "${COMPOSE[@]}" up -d web-init
        ;;

    ""|-h|--help)
        cat <<'EOF'
Usage: bin/stack.sh <command> [args]

Commands:
  up [--logs]      Bring up the full stack: network, then satellites
                   (waited on until healthy), then the app.
  down [args]      Stop and remove containers. Forwarded to
                   `docker compose down` (e.g. `bin/stack.sh down -v` to
                   also remove volumes).
  reset-config     Force setup_configuration to run again on next `up`
                   (e.g. after editing docker/setup_configuration/data.yaml),
                   instead of being skipped as already-completed.
  urls             Print the service URLs shown at the end of `up`, without
                   bringing anything up or down.
  <anything else>  Forwarded to `docker compose` as-is, e.g.:
                     bin/stack.sh ps
                     bin/stack.sh logs -f openklant-web
                     bin/stack.sh exec web bash
EOF
        ;;

    *)
        "${COMPOSE[@]}" "$cmd" "$@"
        ;;
esac
