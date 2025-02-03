#!/bin/sh

set -ex

# Figure out abspath of this script
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

# wait for required services
# See: https://docs.docker.com/compose/startup-order/
${SCRIPTPATH}/wait_for_db.sh

# fixtures_dir=${FIXTURES_DIR:-/app/fixtures}

# Apply database migrations
>&2 echo "Apply database migrations"
python src/manage.py migrate

##
# uWSGI settings
##

# --- Basic Application Configuration
export UWSGI_MODULE="open_inwoner.wsgi"
export UWSGI_CHDIR="src"
export UWSGI_STATIC_MAP="/static=/app/static /media=/app/media"

# --- Process Management
export UWSGI_MASTER=true
export UWSGI_PROCESSES=${UWSGI_PROCESSES:-4}
export UWSGI_THREADS=${UWSGI_THREADS:-8}

# Shutdown gracefully on SIGTERM (common with supervisord and k8s)
export UWSGI_DIE_ON_TERM=true

# We're not hosting multiple apps, so no isolation required
export UWSGI_SINGLE_INTERPRETER=true

# Enable Python threading
export UWSGI_ENABLE_THREADS=true

# --- HTTP Server Settings
export UWSGI_HTTP=${UWSGI_PORT:-8000}
export UWSGI_HTTP_TIMEOUT=${UWSGI_HTTP_TIMEOUT:-120}
export UWSGI_HTTP_KEEPALIVE=true

# --- Request Handling
# Buffer size for POST requests
export UWSGI_POST_BUFFERING=8192

# Internal buffer size
export UWSGI_BUFFER_SIZE=65535

# --- Worker Lifecycle
# Make UWSGI_MAX_REQUESTS explicitly opt-in
if [ -n "${UWSGI_MAX_REQUESTS+x}" ]; then
    if [ "$UWSGI_MAX_REQUESTS" -gt 1 ] 2>/dev/null; then
        export UWSGI_MAX_REQUESTS
    else
        echo "Warning: UWSGI_MAX_REQUESTS must be greater than 1. The variable will be unset."
        unset UWSGI_MAX_REQUESTS
    fi
else
    unset UWSGI_MAX_REQUESTS
fi

# Hard-kill requests after 60 seconds
export UWSGI_HARAKIRI=${UWSGI_HARAKIRI:-60}

# Start Server
>&2 echo "Starting server"
exec uwsgi --show-config --strict
