# This is a multi-stage build file, which means a stage is used to build
# the backend (dependencies), the frontend stack and a final production
# stage re-using assets from the build stages. This keeps the final production
# image minimal in size.

# Stage 1 - Backend build environment
# includes compilers and build tooling to create the environment
FROM python:3.11-slim-bookworm AS backend-build

RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    pkg-config \
    build-essential \
    git \
    libpq-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libxmlsec1-openssl \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    # weasyprint deps (https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#debian-11)
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv
RUN pip install uv -U

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files for dependency resolution
COPY ./pyproject.toml ./uv.lock ./README.rst /app/
COPY ./src /app/src

# Install dependencies
RUN uv sync --frozen --no-dev --compile-bytecode

# Stage 2 - Install frontend deps and build assets
FROM node:20-bookworm-slim AS frontend-build

WORKDIR /app

# copy configuration/build files
COPY ./build /app/build/
COPY ./*.json ./*.js ./.babelrc /app/

# install WITH dev tooling
RUN npm ci --legacy-peer-deps

# copy source code
COPY ./src /app/src

# build frontend
RUN npm run build

# Stage 3 - Build docker image suitable for production
FROM python:3.11-slim-bookworm

# Stage 3.1 - Set up the needed production dependencies
# Note: mime-support becomes media-types in Debian Bullseye (required for correctly serving mime-types for images)
# Also install the dependencies for GeoDjango
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    curl \
    procps \
    nano \
    mime-support \
    postgresql-client \
    libgdal32 \
    libgeos-c1v5 \
    libproj25 \
    libxmlsec1-dev \
    libxmlsec1-openssl \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    gettext \
    shared-mime-info \
    # weasyprint deps (https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#debian-11)
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY ./bin/docker_start.sh /start.sh
COPY ./bin/wait_for_db.sh /wait_for_db.sh
COPY ./bin/celery_worker.sh /celery_worker.sh
COPY ./bin/celery_beat.sh /celery_beat.sh
COPY ./bin/celery_monitor.sh /celery_monitor.sh
COPY ./bin/setup_configuration.sh /setup_configuration.sh
RUN mkdir /app/log /app/media /app/private_media /app/tmp
COPY ./bin/check_celery_worker_liveness.py ./bin/

# prevent writing to the container layer, which would degrade performance.
# This also serves as a hint for the intended volumes.
VOLUME ["/app/log", "/app/media", "/app/private_media"]

# copy backend build deps
COPY --from=backend-build /app/.venv/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-build /app/.venv/bin/uwsgi /usr/local/bin/uwsgi
COPY --from=backend-build /app/.venv/bin/celery /usr/local/bin/celery

# copy frontend build statics
COPY --from=frontend-build /app/src/open_inwoner/static /app/src/open_inwoner/static

# copy source code
COPY ./src /app/src

RUN useradd -M -u 1000 maykin
RUN chown -R maykin /app

# drop privileges
USER maykin

ARG RELEASE COMMIT_HASH
ENV GIT_SHA=${COMMIT_HASH}
ENV RELEASE=${RELEASE}

ENV DJANGO_SETTINGS_MODULE=open_inwoner.conf.docker

ENV DIGID_MOCK=True
ENV EHERKENNING_MOCK=True

ARG SECRET_KEY=dummy

LABEL org.label-schema.vcs-ref=$COMMIT_HASH \
    org.label-schema.vcs-url="https://github.com/maykinmedia/open-inwoner" \
    org.label-schema.version=$RELEASE \
    org.label-schema.name="Open Inwoner"

# Run collectstatic and compilemessages, so the result is already included in
# the image
RUN python src/manage.py collectstatic --noinput \
    && python src/manage.py compilemessages

EXPOSE 8000
CMD ["/start.sh"]
