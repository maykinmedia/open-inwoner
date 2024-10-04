#!/bin/bash

delete_path=$(realpath ./tests/cassettes)

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

pytest --with-openklant-service --record-mode=all -vvv
