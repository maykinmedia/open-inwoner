#!/bin/bash

# Remove any existing environments and lock files
rm -rf .venv uv.lock

# First generate a lock file resolved by uv from the project dependencies 
uv sync --dev

# Find all .txt files in requirements/ and extract package==version pairs so we can
# lock them individually, to ensure we get a uv.lock that matches as closely as possible the
# requirements.txt files.
for req_file in requirements/*.txt; do
    if [ -f "$req_file" ]; then
        echo "Processing $req_file..."

        # Extract lines with package==version (excluding comments and git packages)
        grep -E "^[a-zA-Z0-9][a-zA-Z0-9_-]*==" "$req_file" | while read -r line; do
            package_version=$(echo "$line" | cut -d' ' -f1)
            if [ -n "$package_version" ]; then
                echo "Locking $package_version"
                uv lock --upgrade-package "$package_version" --quiet || echo "Failed to lock $package_version"
            fi
        done
    fi
done

# Re-sync the environment
uv sync --dev
