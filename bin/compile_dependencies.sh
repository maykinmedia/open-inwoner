#!/bin/bash

#
# Compile the dependencies for production, CI and development.
#
# Usage, in the root of the project:
#
#     ./bin/compile_dependencies.sh
#
# Any extra flags/arguments passed to this wrapper script are passed down to uv pip compile.
# E.g. to update a package:
#
#     ./bin/compile_dependencies.sh --upgrade-package django

set -ex

toplevel=$(git rev-parse --show-toplevel)

cd $toplevel

export CUSTOM_COMPILE_COMMAND="./bin/compile_dependencies.sh"

# Base (& prod) deps
uv pip compile --no-strip-extras --python 3.13 \
    --no-emit-index-url \
    --output-file requirements/base.txt \
    "$@" \
    requirements/base.in

# Dependencies for testing
uv pip compile --no-strip-extras --python 3.13 \
    --no-emit-index-url \
    --output-file requirements/ci.txt \
    "$@" \
    requirements/base.txt \
    requirements/test-tools.in \
    requirements/docs.in

# Dev dependencies - exact same set as CI + some extra tooling
uv pip compile --no-strip-extras --python 3.13 \
    --no-emit-index-url \
    --output-file requirements/dev.txt \
    "$@" \
    requirements/ci.txt \
    requirements/dev.in
