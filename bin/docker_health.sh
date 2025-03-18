#!/bin/sh

set -ex

status=$(exec curl -X OPTIONS http://localhost:$PORT/admin -s -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time 5)
[ "$status" -eq 200 ] || exit 1
