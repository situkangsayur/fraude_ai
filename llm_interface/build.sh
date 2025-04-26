#!/bin/bash

# Get the project version from pyproject.toml
PROJECT_VERSION=$(poetry version -s)
# Get the common package version (assuming it's in the parent directory)
COMMON_VERSION=$(cd ../common && poetry version -s)

echo "Building llm_interface version ${PROJECT_VERSION} with common version ${COMMON_VERSION}"

# Build the distribution zip file
poetry build