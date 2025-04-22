#!/bin/bash

# Get the project version from pyproject.toml
PROJECT_VERSION=$(poetry version -s)
# Get the common package version (assuming it's in the parent directory)
COMMON_VERSION=$(cd ../common && poetry version -s)

echo "Building graph_service version ${PROJECT_VERSION} with common version ${COMMON_VERSION}"

# Build the distribution zip file
poetry build

# Build the Docker image from the parent directory, passing versions as build arguments
# Use -f to specify the Dockerfile location relative to the build context (parent dir)
cd .. # Go up to the root directory
docker build \
    --build-arg PROJECT_VERSION=${PROJECT_VERSION} \
    --build-arg COMMON_VERSION=${COMMON_VERSION} \
    -t graph_service:${PROJECT_VERSION} \
    -f graph_service/Dockerfile \
    . # Build context is now the root directory
cd graph_service # Go back to the original directory (optional, but good practice)