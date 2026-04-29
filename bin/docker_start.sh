#!/bin/sh

set -ex

OTEL_SERVICE_NAME="${OTEL_SERVICE_NAME:-openinwoner-web}"

# Figure out abspath of this script
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

# Copy static root to volume, if required
if [ -n "$STATIC_ROOT_VOLUME" ]; then
    cp -r /app/static/* "$STATIC_ROOT_VOLUME"
fi

# wait for required services
# See: https://docs.docker.com/compose/startup-order/
${SCRIPTPATH}/wait_for_db.sh

# fixtures_dir=${FIXTURES_DIR:-/app/fixtures}

# Apply database migrations
>&2 echo "Apply database migrations"
python src/manage.py migrate

# Ensure all mail-editor templates exist in the database
>&2 echo "Loading mail templates"
python src/manage.py add_missing_templates

##
# uWSGI settings
##

# --- Basic Application Configuration
export UWSGI_MODULE="open_inwoner.wsgi"
export UWSGI_CHDIR="src"

# --- Process Management
# Allow for better worker coordination and graceful shutdowns for unresponsive workers
export UWSGI_MASTER=1
export UWSGI_PROCESSES=${UWSGI_PROCESSES:-4}
export UWSGI_THREADS=${UWSGI_THREADS:-8}

# Shutdown gracefully on SIGTERM, which is used by both Docker and k8s to stop containers
export UWSGI_DIE_ON_TERM=1

# We're not hosting multiple apps, so no interpreter isolation should be required
export UWSGI_SINGLE_INTERPRETER=1

# Enable Python threading support
export UWSGI_ENABLE_THREADS=1

# --- HTTP Settings
export UWSGI_HTTP=0.0.0.0:${PORT:-8000}
export UWSGI_HTTP_KEEPALIVE=${UWSGI_HTTP_KEEPALIVE:-1}
export UWSGI_HTTP_TIMEOUT=${UWSGI_HTTP_TIMEOUT:-120}

# Hard-kill requests after 125 seconds (slightly longer than the default timeout)
export UWSGI_HARAKIRI=${UWSGI_HARAKIRI:-125}

# Periodically recycle workers
export UWSGI_MAX_REQUESTS=${UWSGI_MAX_REQUESTS:-100}

# --- Request Handling
# Buffer size for POST requests (in bytes)
export UWSGI_POST_BUFFERING=${UWSGI_POST_BUFFERING:-8192}

# Internal buffer size (in bytes)
export UWSGI_BUFFER_SIZE=${UWSGI_BUFFER_SIZE:-65535}

# Start Server
>&2 echo "Starting server"
exec uwsgi \
    --show-config \
    --strict \
    --static-map /static=/app/static \
    --static-map /media=/app/media
