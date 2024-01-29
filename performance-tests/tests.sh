#!/bin/sh

# branch_name=$(git rev-parse --abbrev-ref HEAD)
commit=$(git rev-parse --short HEAD)
locust \
    --host http://localhost:8000 \
    --bsn 111111110 \
    --run-time 60s \
    --headless \
    --only-summary \
    --csv="results/${commit}"
