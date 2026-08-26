#!/bin/bash
#
# Manage the full local Open Inwoner stack: the main app plus every
# satellite service it talks to, plus the observability stack. Run with no
# arguments for usage; see docs/installation/docker-compose.rst for the full
# picture and how to bring stacks up individually.

usage() {
    cat <<'EOF'
Usage: bin/stack.sh <command> [args]

Commands:
  up [--logs]      Bring up the full stack: network, then satellites/backing
                   services in the background, then the app once its own
                   db/redis/elasticsearch/image are ready, then a ZGW import
                   + search index rebuild once Open Zaak/Objects are
                   healthy. `--logs` follows the app's logs afterwards.
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
}

set -e

SCRIPT=$(readlink -f "$0")
REPO_ROOT=$(dirname "$(dirname "$SCRIPT")")
cd "$REPO_ROOT"

# --project-directory pins path resolution to the repo root, regardless of
# `include:`/`-f` order -- see docker-compose.dev.yml's header.
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

wait_for_completion() {
    # Polls a one-shot container until it exits, failing on a non-zero exit
    # code. `docker compose up --wait` treats an already-exited container as
    # failed even on exit 0, so it can't be used here.
    local service="$1"
    local timeout="${2:-120}"
    local waited=0
    local cid=""

    while [ "$waited" -lt "$timeout" ]; do
        cid=$("${COMPOSE[@]}" ps -a -q "$service")
        if [ -n "$cid" ] && [ "$(docker inspect -f '{{.State.Status}}' "$cid")" = "exited" ]; then
            break
        fi
        sleep 1
        waited=$((waited + 1))
    done

    if [ -z "$cid" ] || [ "$(docker inspect -f '{{.State.Status}}' "$cid")" != "exited" ]; then
        echo "==> Timed out waiting for $service to finish" >&2
        return 1
    fi

    local exit_code
    exit_code=$(docker inspect -f '{{.State.ExitCode}}' "$cid")
    if [ "$exit_code" != "0" ]; then
        echo "==> $service exited with code $exit_code -- check 'bin/stack.sh logs $service'" >&2
        return 1
    fi
}

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
        # Enable OTEL by default
        export OTEL_SDK_DISABLED=false

        echo "==> Ensuring the shared open-inwoner-dev network exists"
        bin/ensure_dev_network.sh

        echo
        echo "==> Building the app image in the background"
        # Explicit rebuild so a stale image never silently runs
        # setup_configuration against outdated code. Backgrounded, since it
        # doesn't need anything else here to happen first; `--quiet` keeps
        # its output from interleaving with everything else starting up
        # below, while still surfacing a build failure.
        "${COMPOSE[@]}" build --quiet web &
        build_pid=$!

        echo
        echo "==> Starting satellites, backing services and observability in the background"
        # setup_configuration only writes config rows pointing at the
        # satellites (see docker/setup_configuration/data.yaml), it never
        # calls them live, so nothing here needs waiting on -- same for
        # observability, which nothing depends on at all. Celery workers
        # aren't listed: they come up later via the full-stack `up -d`.
        "${COMPOSE[@]}" up -d \
            db \
            redis \
            elasticsearch \
            clamav \
            mailpit \
            keycloak \
            openzaak-web \
            objecttypes-web \
            objects-web \
            personen-mock \
            openklant-web \
            openafval-web \
            loki \
            prometheus \
            promtail \
            tempo \
            otel-collector \
            grafana

        # One-shot loaddata jobs; waited on concurrently (see
        # wait_for_completion).
        "${COMPOSE[@]}" up -d openklant-seed openafval-seed
        echo "    waiting for openklant-seed and openafval-seed to finish seeding..."
        wait_for_completion openklant-seed &
        openklant_seed_pid=$!
        wait_for_completion openafval-seed &
        openafval_seed_pid=$!
        seed_failed=0
        wait "$openklant_seed_pid" || seed_failed=1
        wait "$openafval_seed_pid" || seed_failed=1
        [ "$seed_failed" -eq 0 ] || exit 1

        echo
        echo "==> Waiting for the app's own database, redis and elasticsearch"
        # web-init needs these to run migrate and start at all.
        "${COMPOSE[@]}" up -d --wait db redis elasticsearch

        echo
        echo "==> Waiting for the app image build to finish"
        wait "$build_pid" || exit 1

        echo
        echo "==> Starting the main app stack (web-init will now configure it)"
        "${COMPOSE[@]}" up -d

        echo
        echo "==> Waiting for Open Zaak/Objects APIs before triggering the ZGW import below"
        "${COMPOSE[@]}" up -d --wait openzaak-web objecttypes-web objects-web

        echo
        echo "==> Triggering a ZGW data import and search index rebuild"
        # Normally daily via celery-beat (CELERY_BEAT_SCHEDULE in
        # conf/base.py); triggered now so a fresh stack has data. `-T` skips
        # TTY allocation since this isn't interactive.
        "${COMPOSE[@]}" exec -T web celery --workdir src --app "open_inwoner.celery" \
            call open_inwoner.openzaak.tasks.import_zgw_data
        "${COMPOSE[@]}" exec -T web celery --workdir src --app "open_inwoner.celery" \
            call open_inwoner.search.tasks.rebuild_search_index

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
        # web-init is one-shot, not a running service, so its marker (see
        # bin/setup_configuration.sh) can't be removed via `exec` -- use a
        # throwaway container against the same volume instead.
        echo "==> Clearing the setup_configuration marker"
        "${COMPOSE[@]}" run --rm --entrypoint sh web-init -c \
            "rm -f /var/lib/open-inwoner/setup-configuration/.completed"

        echo
        echo "==> Re-running web-init"
        "${COMPOSE[@]}" up -d web-init
        ;;

    ""|-h|--help)
        usage
        ;;

    *)
        "${COMPOSE[@]}" "$cmd" "$@"
        ;;
esac
