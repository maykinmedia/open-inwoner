#!/bin/bash
#
# This script will run all tests tagged with "openklant2" and re-record the
# underlying cassettes by dynamically spinning up a live server instance using
# the Openklant2ServiceTestCase test utility and replacing the existing
# cassettes.
#
# Run this script from the root of the repository

set -e

delete_path=$(realpath ./src/open_inwoner/openklant/tests/cassettes)

# Display the full path and ask for confirmation
echo "You are about to recursively delete all VCR cassettes from the following directory:"
echo "$delete_path"
read -p "Are you sure you want to proceed? (y/N): " confirm

if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
    echo "Deleting directory..."
    rm -rf "$delete_path"
    echo "Directory deleted."
else
    echo "Operation cancelled."
    exit 0
fi

set -x
RECORD_OPENKLANT_CASSETTES=1 python src/manage.py test src/open_inwoner --tag openklant2
