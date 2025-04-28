#!/bin/bash

# Get the project version from pyproject.toml
PROJECT_VERSION=$(grep "^version = " pyproject.toml | cut -d'"' -f2)

# Build the distribution zip file
echo "Running poetry build"
poetry build
echo "poetry build completed"

# Build the Docker image
echo "Running docker build"
docker build -t dashboard .
echo "docker build completed"