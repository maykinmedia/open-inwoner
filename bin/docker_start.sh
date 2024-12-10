#!/bin/sh

set -ex

# Figure out abspath of this script
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

# wait for required services
# See: https://docs.docker.com/compose/startup-order/
${SCRIPTPATH}/wait_for_db.sh

# fixtures_dir=${FIXTURES_DIR:-/app/fixtures}

uwsgi_port=${UWSGI_PORT:-8000}
uwsgi_processes=${UWSGI_PROCESSES:-4}
uwsgi_threads=${UWSGI_THREADS:-8}
uwsgi_http_timeout=${UWSGI_HTTP_TIMEOUT:-120}

# Apply database migrations
>&2 echo "Apply database migrations"
python src/manage.py migrate

# Start server
>&2 echo "Starting server"
exec uwsgi \
    --die-on-term \
    --http :$uwsgi_port \
    --http-keepalive \
    --http-timeout $uwsgi_http_timeout \
    --module open_inwoner.wsgi \
    --static-map /static=/app/static \
    --static-map /media=/app/media  \
    --chdir src \
    --enable-threads \
    --processes $uwsgi_processes \
    --threads $uwsgi_threads \
    --post-buffering=8192 \
    --buffer-size=65535
    # processes & threads are needed for concurrency without nginx sitting inbetween
