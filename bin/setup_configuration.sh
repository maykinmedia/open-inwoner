#!/bin/bash

# setup initial configuration using environment variables
# Run this script from the root of the repository

set -e

# Figure out abspath of this script
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

${SCRIPTPATH}/wait_for_db.sh

src/manage.py migrate
src/manage.py setup_configuration \
    --yaml-file /app/setup_configuration/data.yaml
