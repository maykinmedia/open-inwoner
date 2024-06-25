# This is a multi-stage build file, which means a stage is used to build
# the backend (dependencies), the frontend stack and a final production
# stage re-using assets from the build stages. This keeps the final production
# image minimal in size.

# Stage 1 - Backend build environment
# includes compilers and build tooling to create the environment
FROM python:3.11-slim-bookworm AS backend-build

RUN apt-get update && apt-get install -y --no-install-recommends \
        pkg-config \
        build-essential \
        git \
        libpq-dev \
        libxmlsec1-openssl \
        libgdk-pixbuf2.0-0 \
        libffi-dev \
        shared-mime-info \
        # weasyprint deps (https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#debian-11)
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN mkdir /app/src

# Ensure we use the latest version of pip
RUN pip install pip>=24 setuptools -U
COPY ./requirements /app/requirements
RUN pip install -r requirements/production.txt


# Stage 2 - Install frontend deps and build assets
FROM node:20-buster AS frontend-build

RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
    && rm -rf /var/lib/apt/lists/*

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
        vim \
        postgresql-client \
        libgdal32 \
        libgeos-c1v5 \
        libproj25 \
        libxmlsec1-openssl \
        libgdk-pixbuf2.0-0 \
        libffi-dev \
        shared-mime-info \
        mime-support \
        # weasyprint deps (https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#debian-11)
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY ./bin/docker_start.sh /start.sh
COPY ./bin/celery_worker.sh /celery_worker.sh
COPY ./bin/check_celery_worker_liveness.py ./bin/
RUN mkdir /app/log
RUN mkdir /app/media

# copy backend build deps
COPY --from=backend-build /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=backend-build /usr/local/bin/uwsgi /usr/local/bin/uwsgi
COPY --from=backend-build /app/src/ /app/src/
COPY --from=backend-build /usr/local/bin/celery /usr/local/bin/celery

# copy frontend build statics
COPY --from=frontend-build /app/src/open_inwoner/static /app/src/open_inwoner/static

# copy source code
COPY ./src /app/src

RUN useradd -M -u 1000 maykin
RUN chown -R maykin /app

# drop privileges
USER maykin

ARG COMMIT_HASH
ENV GIT_SHA=${COMMIT_HASH}
ENV DJANGO_SETTINGS_MODULE=open_inwoner.conf.docker
ENV DIGID_MOCK=True
ENV EHERKENNING_MOCK=True

ARG SECRET_KEY=dummy

# Run collectstatic, so the result is already included in the image
RUN python src/manage.py collectstatic --noinput

EXPOSE 8000
CMD ["/start.sh"]
