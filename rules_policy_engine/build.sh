#!/bin/bash

# Get the project version from pyproject.toml
PROJECT_VERSION="0.1.0"
# Get the common package version (assuming it's in the parent directory)
COMMON_VERSION="0.1.0"

echo "Building rules_policy_engine version ${PROJECT_VERSION} with common version ${COMMON_VERSION}"

# Build the distribution zip file
echo "Running poetry build"
poetry build
echo "poetry build completed"

# Build the Docker image from the parent directory, passing versions as build arguments
# Use -f to specify the Dockerfile location relative to the build context (parent dir)
echo "Running docker build"
docker build \
    --build-arg PROJECT_VERSION=${PROJECT_VERSION} \
    --build-arg COMMON_VERSION=${COMMON_VERSION} \
    -t rules_policy_engine:${PROJECT_VERSION} \
    -f rules_policy_engine/Dockerfile \
    . # Build context is now the root directory
echo "docker build completed"
cd rules_policy_engine # Go back to the original directory (optional, but good practice)